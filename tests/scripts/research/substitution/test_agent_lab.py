from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[4]
MODULE_PATH = (
    REPOSITORY / "scripts" / "research" / "substitution" / "agent_lab.py"
)
SPEC = importlib.util.spec_from_file_location("na2_substitution_agent_lab", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load {MODULE_PATH}")
LAB = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LAB
SPEC.loader.exec_module(LAB)


class FakeClient:
    def __init__(self, status: str = "paused") -> None:
        self.words: dict[int, int] = {}
        self.vm_status = status
        self.step_calls: list[tuple[int, object]] = []

    def write_u8(self, address: int, value: int) -> None:
        word_address = address & ~3
        shift = (address & 3) * 8
        mask = 0xFF << shift
        self.words[word_address] = (
            self.words.get(word_address, 0) & ~mask
        ) | (value << shift)

    def write_u16(self, address: int, value: int) -> None:
        for offset, byte in enumerate(struct.pack("<H", value & 0xFFFF)):
            self.write_u8(address + offset, byte)

    def write_u32(self, address: int, value: int) -> None:
        self.words[address] = value & 0xFFFFFFFF

    def write_f32(self, address: int, value: float) -> None:
        self.write_u32(address, struct.unpack("<I", struct.pack("<f", value))[0])

    def read(self, address: int, length: int) -> bytes:
        return b"".join(
            struct.pack("<I", self.words.get(current, 0))
            for current in range(address, address + length, 4)
        )

    def status(self) -> str:
        return self.vm_status

    def step_frames(self, frames: int, states: object) -> object:
        self.step_calls.append((frames, states))
        return LAB.PINE.FrameStep(100, 100 + frames)


class AgentLabTests(unittest.TestCase):
    def test_observe_decodes_substitution_inputs(self) -> None:
        client = FakeClient()
        manager = 0x00110000
        fighter = 0x00120000
        opponent = 0x00125000
        input_object = 0x00130000
        history = 0x00140000
        definition = 0x00150000
        opponent_record_base = definition - 2 * LAB.ACTION_RECORD_SIZE
        action = 0x00160000
        fighter_record_base = 0x00170000
        eligibility = 0x00180000
        effect_one = 0x00190000
        effect_two = 0x00190100

        client.write_u32(LAB.MANAGER_POINTER, manager)
        client.write_u32(manager + 0x08, 7)
        client.write_u32(manager + 0x0C, 2)
        client.write_u32(manager + 0x4C, 57)
        client.write_u32(manager + 0xC8, 57)
        client.write_u32(manager + 0xDE4, fighter)
        client.write_u32(manager + 0xDE8, opponent)
        client.write_u32(fighter + 0x24, input_object)
        client.write_u16(fighter + 0x60, 0x0020)
        client.write_u32(fighter + 0x68, 57)
        client.write_f32(fighter + 0x6C, 0.75)
        client.write_f32(fighter + 0x70, 3.0)
        client.write_u32(fighter + 0x94, action)
        client.write_u32(fighter + 0x88, 0x12345678)
        client.write_u16(fighter + 0x18E, 5)
        client.write_u16(fighter + 0x190, 0x30)
        client.write_u16(fighter + 0x192, 1)
        client.write_u8(fighter + 0xA8, 0x43)
        client.write_u32(fighter + 0x338, 0x10000000)
        client.write_u16(fighter + 0xA38, 48)
        client.write_u16(fighter + 0xA3C, 0x17)
        client.write_u32(
            fighter + 0xA4C,
            fighter_record_base + 0x17 * LAB.ACTION_RECORD_SIZE,
        )
        client.write_u32(fighter + 0xA54, fighter_record_base)
        client.write_u16(opponent + 0xA38, 3)
        client.write_u32(opponent + 0xA54, opponent_record_base)
        client.write_u32(opponent + 0x68, 70)
        client.write_u16(fighter + 0x95C, 5)
        client.write_u32(fighter + 0xC74, eligibility)
        client.write_u32(eligibility + 0x0C, 2)
        client.write_u32(fighter + 0x8C4, 2)
        client.write_u32(fighter + 0x8C8, effect_one)
        client.write_u32(effect_one + 0x68, 4)
        client.write_u32(effect_one + 0x1C, effect_two)
        client.write_u32(effect_two + 0x68, 9)
        client.write_u32(fighter + 0xE50, definition)
        client.write_u32(action + 0x18, 0x800)
        client.write_u32(definition + 0x10, 0x000C0000)
        client.write_u32(definition + 0x14, 0)
        client.write_u8(definition + 0x1A, 0xFF)
        client.write_u8(definition + 0x2C, 0x1F)
        client.write_u16(input_object + 0x74, 0x0100)
        client.write_u16(input_object + 0x76, 0x0200)
        client.write_u32(input_object + 0x94, history)
        client.write_u32(input_object + 0x9C, 1)
        client.write_u32(input_object + 0xA0, 2)
        client.write_u32(input_object + 0xAC, 0x10000000)
        client.write_u32(history + 0x18 + 4, 0x0100)

        state = LAB.observe(client)

        p1 = state["fighters"]["p1"]
        self.assertEqual(p1["controller_mode"], 1)
        self.assertEqual(p1["rng_word_88"], "0x12345678")
        self.assertEqual(p1["major_state_18e"], 5)
        self.assertEqual(p1["eligibility_object_c74_state"], 2)
        self.assertEqual(p1["temporary_effects"]["ids"], [4, 9])
        self.assertTrue(p1["temporary_effects"]["has_id_9"])
        self.assertEqual(p1["guard_held_frames_95c"], 5)
        self.assertEqual(
            p1["definitions"]["hit_e50"]["substitution_timing_1a"], -1
        )
        self.assertEqual(
            p1["definitions"]["hit_e50"]["response_selector_2c"], "0x1F"
        )
        self.assertEqual(
            p1["definitions"]["hit_e50"]["substitution_block_flags"],
            "0x00000000",
        )
        self.assertEqual(
            p1["definitions"]["hit_e50"]["record_matches"],
            [
                {
                    "owner": "p2",
                    "character_id": 70,
                    "index": 2,
                    "base": f"0x{opponent_record_base:08X}",
                }
            ],
        )
        self.assertEqual(p1["action_records"]["current_index_a3c"], 0x17)
        self.assertEqual(p1["action"]["flags_18"], "0x00000800")
        self.assertEqual(p1["input"]["history"][0]["word_1"], "0x00000100")

    def test_definition_match_can_include_clean_catalog_identity(self) -> None:
        client = FakeClient()
        definition = 0x00150000
        record_base = definition - 2 * LAB.ACTION_RECORD_SIZE
        client.write_u32(definition + 0x10, 0x000C0000)
        client.write_u8(definition + 0x1A, 0xFF)
        catalog = {
            (70, 2): {
                "record_index_hex": "0x02",
                "timing_address": "0x00524C00",
                "timing_file_offset": "0x424D00",
                "raw_timing": -1,
                "effective_timing": -1,
                "policy": "mt_modulo_1_of_3_current_record",
                "negative_rng_modulus": 3,
                "negative_rng_passing_u32_words": 1431655765,
                "negative_rng_total_u32_words": 1 << 32,
                "response_selector_2c": "0x1F",
                "substitution_block_flags": "0x00000000",
                "runtime_timing_mutated": True,
                "runtime_timing_writers": "FUN_TEST@0x00123456",
                "runtime_timing_values": "-1|0",
                "runtime_substitution_block_mutated": False,
                "runtime_mutation_summary": "test mutation",
                "command_mapping_id": "T1",
                "command_name": "Named Attack",
            }
        }

        state = LAB.definition_state(
            LAB.Memory(client),
            definition,
            {"p2": (record_base, 3, 70)},
            catalog,
        )

        self.assertEqual(
            state["record_matches"][0]["catalog"]["command_name"],
            "Named Attack",
        )
        self.assertTrue(
            state["record_matches"][0]["catalog"]["runtime_timing_mutated"]
        )
        self.assertEqual(
            state["record_matches"][0]["catalog"]["runtime_timing_writers"],
            "FUN_TEST@0x00123456",
        )

    def test_pad_parser_builds_atomic_full_state(self) -> None:
        slot, state = LAB.pad_spec("0=r2,cross")
        self.assertEqual(slot, 0)
        self.assertEqual(len(state.data), 18)
        self.assertEqual(state.data[1], 0xBD)

    def test_observe_rejects_a_moving_vm(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "requires a paused VM"):
            LAB.observe(FakeClient("running"))

    def test_running_step_returns_status_without_paused_observation(self) -> None:
        client = FakeClient("running")
        states = {0: LAB.PadState.neutral()}
        with patch.object(LAB, "observe") as observer:
            output = LAB.step_output(client, 1, states)

        observer.assert_not_called()
        self.assertEqual(client.step_calls, [(1, states)])
        self.assertEqual(output["vm_status"], "running")
        self.assertEqual(
            output["frame_step"], {"start": 100, "end": 101, "count": 1}
        )

    def test_paused_step_retains_rich_observation(self) -> None:
        client = FakeClient("paused")
        states = {0: LAB.PadState.neutral()}
        observation = {"vm_status": "paused", "battle_active": True}
        catalog: dict[tuple[int, int], dict[str, object]] = {}
        with patch.object(LAB, "observe", return_value=observation) as observer:
            output = LAB.step_output(client, 2, states, catalog)

        observer.assert_called_once_with(client, catalog)
        self.assertEqual(client.step_calls, [(2, states)])
        self.assertTrue(output["battle_active"])
        self.assertEqual(
            output["frame_step"], {"start": 100, "end": 102, "count": 2}
        )


if __name__ == "__main__":
    unittest.main()
