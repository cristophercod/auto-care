"""
tests/test_services.py
----------------------
Testes automáticos da lógica (sem interface). Rode com:
    python -m unittest discover -s tests -v
Usam um banco temporário, então NÃO mexem nos seus dados reais.
"""
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import database  # noqa: E402
from core.validators import ValidationError  # noqa: E402
from services import maintenances as mnt  # noqa: E402
from services import reports, schedules, vehicles  # noqa: E402


def br(d):  # date -> 'dd/mm/aaaa'
    return d.strftime("%d/%m/%Y")


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUTOTRACK_DB"] = str(Path(self.tmp.name) / "test.db")
        database.init_db()

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("AUTOTRACK_DB", None)

    def new_vehicle(self, plate="ABC-1234", km=50000):
        return vehicles.create_vehicle("Fiat", "Uno", 2015, plate, km, "Flex")


class ValidatorTests(unittest.TestCase):
    def test_brazilian_number_formats(self):
        from core import validators as v
        self.assertEqual(v.validate_money("1.250,50"), 1250.50)
        self.assertEqual(v.validate_money("350"), 350.0)
        self.assertEqual(v.validate_money("R$ 99,9"), 99.9)
        self.assertEqual(v.validate_km("45.000"), 45000)
        self.assertEqual(v.validate_km("45000 km"), 45000)

    def test_empty_and_invalid_numbers_are_rejected(self):
        from core import validators as v
        for bad in ("", "   ", None, "-5", "abc", "45,5", "12..3"):
            with self.assertRaises(ValidationError, msg=repr(bad)):
                v.validate_km(bad)
        for bad in ("", None, "-1", "abc"):
            with self.assertRaises(ValidationError, msg=repr(bad)):
                v.validate_money(bad)
        self.assertEqual(v.validate_money("0"), 0.0)          # serviço gratuito é válido
        self.assertIsNone(v.validate_km("", "Km", required=False))

    def test_dates(self):
        from core import validators as v
        self.assertEqual(v.parse_date("15/03/2026", "Data"), date(2026, 3, 15))
        for bad in ("31/02/2026", "abc", "2026/03/15", "15/03/1800"):
            with self.assertRaises(ValidationError, msg=bad):
                v.parse_date(bad, "Data")


class VehicleTests(BaseTest):
    def test_text_fields_from_the_form(self):
        vid = vehicles.create_vehicle("Fiat", "Uno", "2015", "abc-1234", "50.000", "Flex")
        self.assertEqual(vehicles.get_vehicle(vid)["current_km"], 50000)
        with self.assertRaises(ValidationError) as ctx:        # campos vazios nunca viram 0
            vehicles.create_vehicle("Fiat", "Uno", "", "ABC9999", "", None)
        self.assertEqual(len(ctx.exception.messages), 2)

    def test_create_and_list(self):
        vid = self.new_vehicle()
        v = vehicles.get_vehicle(vid)
        self.assertEqual(v["plate"], "ABC1234")
        self.assertEqual(len(vehicles.list_vehicles()), 1)

    def test_mercosul_plate_ok_and_duplicate_blocked(self):
        vehicles.create_vehicle("VW", "Gol", 2020, "abc1d23", 10, None)
        with self.assertRaises(ValidationError):
            vehicles.create_vehicle("VW", "Gol", 2020, "ABC-1D23", 10, None)

    def test_invalid_data_reports_all_errors(self):
        with self.assertRaises(ValidationError) as ctx:
            vehicles.create_vehicle("", "Uno", 1800, "12", -5, None)
        self.assertGreaterEqual(len(ctx.exception.messages), 4)

    def test_update_and_delete_cascade(self):
        vid = self.new_vehicle()
        vehicles.update_vehicle(vid, "Fiat", "Palio", 2016, "ABC1234", 60000, "Etanol")
        self.assertEqual(vehicles.get_vehicle(vid)["model"], "Palio")
        mnt.create_maintenance(vid, "Troca de óleo", "Óleo 5W30", br(date.today()), 60000, 200, None)
        schedules.create_schedule(vid, "Pneus", None, 70000)
        self.assertEqual(vehicles.count_related(vid), (1, 1))
        vehicles.delete_vehicle(vid)
        self.assertEqual(mnt.list_maintenances(), [])
        self.assertEqual(schedules.list_schedules(), [])


class MaintenanceTests(BaseTest):
    def test_create_updates_vehicle_km(self):
        vid = self.new_vehicle(km=50000)
        res = mnt.create_maintenance(vid, "Freios", "Pastilhas", br(date.today()), 52000, 350.5, "Oficina X")
        self.assertTrue(res["km_updated"])
        self.assertEqual(vehicles.get_vehicle(vid)["current_km"], 52000)
        res = mnt.create_maintenance(vid, "Filtros", "Filtro de ar", br(date.today()), 40000, 80, None)
        self.assertFalse(res["km_updated"])

    def test_validations(self):
        vid = self.new_vehicle()
        future = br(date.today() + timedelta(days=3))
        with self.assertRaises(ValidationError):
            mnt.create_maintenance(vid, "Freios", "Pastilhas", future, 100, 10, None)
        with self.assertRaises(ValidationError):
            mnt.create_maintenance(vid, "Freios", "Pastilhas", br(date.today()), 100, -10, None)
        with self.assertRaises(ValidationError):
            mnt.create_maintenance(None, "", "", "31/02/2020", -1, None, None)

    def test_filters_edit_delete(self):
        v1, v2 = self.new_vehicle("AAA1111"), self.new_vehicle("BBB2222")
        today = date.today()
        a = mnt.create_maintenance(v1, "Troca de óleo", "Óleo", br(today - timedelta(days=40)), 50000, 100, None)["id"]
        mnt.create_maintenance(v2, "Pneus", "4 pneus", br(today - timedelta(days=5)), 50000, 1200, None)
        self.assertEqual(len(mnt.list_maintenances(vehicle_id=v1)), 1)
        self.assertEqual(len(mnt.list_maintenances(service_type="pneus")), 1)
        self.assertEqual(len(mnt.list_maintenances(date_from=today - timedelta(days=10))), 1)
        self.assertEqual(len(mnt.list_maintenances(search="óleo")), 1)
        mnt.update_maintenance(a, v1, "Troca de óleo", "Óleo sintético", br(today), 50500, 150, "Posto Y")
        self.assertEqual(mnt.get_maintenance(a)["cost"], 150)
        mnt.delete_maintenance(a)
        self.assertIsNone(mnt.get_maintenance(a))


class ScheduleTests(BaseTest):
    def test_compute_status_by_date(self):
        ref = date(2026, 1, 15)
        self.assertEqual(schedules.compute_status(ref - timedelta(days=2), None, 0, 30, 1000, ref)[0], "atrasada")
        self.assertEqual(schedules.compute_status(ref + timedelta(days=10), None, 0, 30, 1000, ref)[0], "proxima")
        self.assertEqual(schedules.compute_status(ref + timedelta(days=90), None, 0, 30, 1000, ref)[0], "no_prazo")

    def test_compute_status_by_km(self):
        ref = date(2026, 1, 15)
        self.assertEqual(schedules.compute_status(None, 50000, 50001, 30, 1000, ref)[0], "atrasada")
        self.assertEqual(schedules.compute_status(None, 50000, 50000, 30, 1000, ref)[0], "atrasada")
        self.assertEqual(schedules.compute_status(None, 50000, 49500, 30, 1000, ref)[0], "proxima")
        self.assertEqual(schedules.compute_status(None, 50000, 40000, 30, 1000, ref)[0], "no_prazo")

    def test_worst_criterion_wins(self):
        ref = date(2026, 1, 15)
        status, _ = schedules.compute_status(ref + timedelta(days=200), 50000, 51000, 30, 1000, ref)
        self.assertEqual(status, "atrasada")

    def test_requires_date_or_km(self):
        vid = self.new_vehicle()
        with self.assertRaises(ValidationError):
            schedules.create_schedule(vid, "Pneus", "", None)

    def test_list_sorted_done_and_settings(self):
        vid = self.new_vehicle(km=50000)
        today = date.today()
        ok = schedules.create_schedule(vid, "Filtros", br(today + timedelta(days=200)), None)
        late = schedules.create_schedule(vid, "Pneus", br(today - timedelta(days=3)), None)
        soon = schedules.create_schedule(vid, "Freios", None, 50500)
        items = schedules.list_schedules()
        self.assertEqual([i["id"] for i in items], [late, soon, ok])
        schedules.set_done(late, True)
        self.assertEqual(len(schedules.list_schedules()), 2)
        self.assertEqual(len(schedules.list_schedules(include_done=True)), 3)
        schedules.set_done(late, False)
        schedules.save_alert_settings(10, 100)
        self.assertEqual(schedules.get_alert_settings(), (10, 100))
        self.assertEqual({i["id"]: i["status"] for i in schedules.list_schedules()}[soon], "no_prazo")
        with self.assertRaises(ValidationError):
            schedules.save_alert_settings(-1, 100)


class ReportTests(BaseTest):
    def test_dashboard_and_expenses(self):
        v1, v2 = self.new_vehicle("AAA1111"), self.new_vehicle("BBB2222")
        today = date.today()
        mnt.create_maintenance(v1, "Pneus", "Pneus", br(today - timedelta(days=60)), 50000, 1000, None)
        mnt.create_maintenance(v1, "Freios", "Freios", br(today - timedelta(days=2)), 50100, 500, None)
        schedules.create_schedule(v2, "Revisão geral", br(today - timedelta(days=1)), None)
        d = reports.dashboard_summary()
        self.assertEqual((d["vehicles"], d["maintenances"], d["total_spent"], d["overdue"]), (2, 2, 1500, 1))
        e = reports.expenses_summary()
        self.assertEqual((e["total"], e["services"], e["average"]), (1500, 2, 750))
        e = reports.expenses_summary(date_from=today - timedelta(days=10))
        self.assertEqual((e["total"], len(e["by_vehicle"])), (500, 2))   # v2 aparece com R$ 0
        self.assertEqual(reports.expenses_summary(date_to=today - timedelta(days=100))["total"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
