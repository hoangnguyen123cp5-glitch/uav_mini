import csv
import importlib.util
import math
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class LogTests(unittest.TestCase):
    def analyze(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "test.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["t", "attitude.x", "attitude.y", "attitude.z",
                                 "attitudeTarget.x", "attitudeTarget.y", "attitudeTarget.z"])
                writer.writerows(rows)
            return module("analyze_log").analyze(path)

    def test_known_rmse(self):
        result = self.analyze([[0, math.radians(3), 0, 0, 0, 0, 0],
                               [0.01, math.radians(4), 0, 0, 0, 0, 0]])
        self.assertAlmostEqual(result["tracking_error_deg"]["roll"]["rmse"], math.sqrt(12.5))
        self.assertAlmostEqual(result["median_log_rate_hz"], 100)

    def test_yaw_wrap_and_ring_buffer(self):
        a, b = math.radians(179), math.radians(-179)
        result = self.analyze([[1, 0, 0, a, 0, 0, b], [0, 0, 0, a, 0, 0, b]])
        self.assertAlmostEqual(result["tracking_error_deg"]["yaw"]["rmse"], 2)
        self.assertTrue(result["reordered_ring_buffer"])

    def test_duplicate_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.analyze([[0] * 7, [0] * 7])

    def test_nan_rejected(self):
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            self.analyze([[0] * 7, [1, float("nan"), 0, 0, 0, 0, 0]])

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, "At least"):
            self.analyze([])

    def test_gap_detection(self):
        result = self.analyze([[t, 0, 0, 0, 0, 0, 0] for t in [0, .01, .02, .06]])
        self.assertEqual(result["gaps_over_1_5_median"], 1)


class BenchDriverTests(unittest.TestCase):
    def test_outputs_remain_low_despite_mutated_parameters_and_demands(self):
        # Compile the actual output-driver source, not a reimplementation.
        source = r'''
#include <cassert>
#include <cmath>
#include <cstdarg>
#include <vector>
#define LOW 0
#define OUTPUT 1
std::vector<int> touched;
void digitalWrite(int pin, int value) {
    assert(pin >= 4 && pin <= 7); assert(value == LOW); touched.push_back(pin);
}
void pinMode(int pin, int mode) { assert(pin >= 4 && pin <= 7); assert(mode == OUTPUT); }
void print(const char *, ...) {}
'''
        source += (ROOT / "firmware/bench_motors.ino").read_text()
        source += r'''
int main() {
    setupMotors();
    for (int i = 0; i < 4; ++i) motorPins[i] = 19 + i;
    pwmStop = 1023; pwmMax = 2000; pwmResolution = -50;
    for (float demand : {0.0f, 1.0f, -1.0f, INFINITY, NAN}) {
        for (float &m : motors) m = demand;
        sendMotors(); assert(getDutyCycle(demand) == 0);
    }
    testMotor(-1, 1); testMotor(4, 1); testMotor(0, NAN);
    for (float m : motors) assert(m == 0);
    assert(!touched.empty());
    for (int pin : {4, 5, 6, 7}) {
        bool found = false;
        for (int p : touched) if (p == pin) found = true;
        assert(found);
    }
}
'''
        with tempfile.TemporaryDirectory() as folder:
            src = pathlib.Path(folder) / "bench.cpp"
            exe = pathlib.Path(folder) / "bench"
            src.write_text(source)
            subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


class PreparationTests(unittest.TestCase):
    def test_unknown_upstream_hook_rejected(self):
        with self.assertRaises(ValueError):
            module("prepare_firmware").replace_once("unexpected", "old", "new", "test")

    def test_ambiguous_upstream_hook_rejected(self):
        with self.assertRaises(ValueError):
            module("prepare_firmware").replace_once("old old", "old", "new", "test")


if __name__ == "__main__":
    unittest.main()
