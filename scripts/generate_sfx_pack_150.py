#!/usr/bin/env python3
"""Studio-grade deterministic Python DSP generator for 150 CC0 UI & Arcade SFX (WAV + OGG)."""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import subprocess
import sys
import wave
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import signal

SR = 44100
ROOT = Path(__file__).resolve().parent.parent
SLUG = "ui-arcade-sfx-150"
REL_DIR = ROOT / "releases" / SLUG
WORK_DIR = REL_DIR / "work_tmp"
WAV_DIR = WORK_DIR / "wav"
OGG_DIR = WORK_DIR / "ogg"
DOCS_PACK_DIR = ROOT / "docs" / "packs" / SLUG
SAMPLES_DIR = DOCS_PACK_DIR / "samples"
SS_DIR = REL_DIR / "screenshots"

CC0_LICENSE = """CC0 1.0 Universal (Public Domain Dedication) — Each-Touch Asset Lab

Every audio file in this pack (WAV and OGG) was procedurally synthesized using
deterministic mathematical DSP algorithms (zero generative AI, zero third-party samples).

To the extent possible under law, Each-Touch Asset Lab waives all copyright and
related or neighboring rights to these sound files. You may use, edit, redistribute,
and include them in free or commercial games, videos, apps, and software with no
royalties and no attribution required.

Storefront: https://each-touch.github.io/asset-lab/
"""

UPGRADE_NOTE = """Thank you for downloading the Free 20-SFX Demo from Each-Touch Asset Lab!

Included in this Demo:
- 20 studio-mastered CC0 sounds (2 from each of the 10 categories) in both 44.1kHz 16-bit WAV & OGG Vorbis.

Upgrade to the Full 150-SFX Mega-Pack ($2.99 USD):
- All 150 unique sounds across 10 folders (300 WAV + OGG files)
- Full CSV tracklist + JSON metadata manifest + CC0 commercial dedication

Get the Full Pack: https://each-touch.itch.io/150-cc0-ui-arcade-sfx-pack
Audition all categories online: https://each-touch.github.io/asset-lab/
"""

CATEGORIES = [
    ("01_UI_Clicks", "UI Clicks & Ticks", [
        "mechanical_crisp", "glass_tap", "soft_pop", "tactile_switch", "micro_snap",
        "wooden_key", "metal_pin", "bubble_bloop", "tab_toggle_on", "tab_toggle_off",
        "card_tick", "scroll_notch", "menu_select", "focus_pip", "arcade_blip",
    ]),
    ("02_UI_Confirm_Success", "UI Confirm & Success", [
        "chime_bright", "bell_two_note", "glass_resolve", "warm_chord", "quest_complete",
        "save_sparkle", "unlock_ping", "level_ready", "badge_award", "major_triad",
        "soft_affirm", "crystal_confirm", "upgrade_ding", "sync_complete", "gold_seal",
    ]),
    ("03_UI_Alerts_Errors", "UI Alerts & Errors", [
        "soft_deny", "two_tone_buzz", "warning_ping", "locked_thud", "invalid_chirp",
        "glitch_reject", "low_alarm", "cancel_drop", "cooldown_tick", "access_denied",
        "muted_error", "short_siren", "alert_double", "empty_slot", "system_fault",
    ]),
    ("04_Coins_Pickups_Gems", "Coins, Pickups & Gems", [
        "classic_coin", "silver_coin", "gold_stack", "emerald_gem", "diamond_spark",
        "xp_orb_small", "xp_orb_large", "heart_pickup", "key_collect", "star_chime",
        "loot_drop", "mana_crystal", "combo_coin_high", "chest_sparkle", "relic_found",
    ]),
    ("05_Jumps_Hops_Movement", "Jumps, Hops & Movement", [
        "spring_jump", "arcade_hop", "double_jump", "air_dash", "dodge_roll",
        "heavy_land", "light_step", "wall_kick", "swim_stroke", "rope_snap",
        "bounce_pad", "slide_skid", "climb_grab", "jet_burst", "teleport_step",
    ]),
    ("06_Lasers_Blasters_SciFi", "Lasers, Blasters & Sci-Fi", [
        "pew_classic", "plasma_bolt", "railgun_zap", "pulse_rifle", "ion_beam",
        "shield_hum_zap", "alien_chirp", "warp_shot", "phaser_sweep", "stun_dart",
        "overcharge_fire", "hyper_laser", "ricochet_zap", "scanner_beam", "turret_burst",
    ]),
    ("07_Impacts_Hits_Punches", "Impacts, Hits & Punches", [
        "heavy_punch", "light_jab", "sword_slash_hit", "shield_clang", "armor_thud",
        "crit_strike", "wood_knock", "stone_crack", "parry_ring", "slap_snap",
        "body_fall", "arrow_thunk", "ice_shatter_hit", "boss_stomp", "brick_break",
    ]),
    ("08_Explosions_Booms", "Explosions & Booms", [
        "sub_boom", "retro_crunch", "grenade_pop", "barrel_blast", "distant_thunder",
        "ship_core_boom", "mine_detonate", "rocket_impact", "fireball_poof", "cluster_burst",
        "shockwave_thump", "cannon_blast", "debris_scatter", "nuke_rumble", "spark_crack_boom",
    ]),
    ("09_Powerups_LevelUp", "Powerups & Level Up", [
        "fanfare_rise", "hero_level_up", "shield_charge", "speed_boost", "rage_aura",
        "mana_surge", "skill_unlock", "health_regen", "combo_max", "magic_buff",
        "reactor_online", "tier_ascend", "star_power", "overdrive_on", "victory_sting",
    ]),
    ("10_Menus_Swoosh_Transitions", "Menus, Swooshes & Transitions", [
        "silk_whoosh", "drawer_open", "drawer_close", "page_flip", "modal_pop_in",
        "modal_pop_out", "swipe_fast", "curtain_sweep", "wind_gust_short", "shimmer_fade",
        "panel_zip", "time_warp_in", "hover_glide", "card_deal", "transition_flash",
    ]),
]


def _butter_filter(x: np.ndarray, kind: str, cutoff_hz: float, order: int = 2) -> np.ndarray:
    nyq = SR * 0.5
    wn = float(np.clip(cutoff_hz / nyq, 0.002, 0.95))
    sos = signal.butter(order, wn, btype=kind, output="sos")
    return signal.sosfilt(sos, x)


def _bandpass(x: np.ndarray, lo_hz: float, hi_hz: float, order: int = 2) -> np.ndarray:
    nyq = SR * 0.5
    w1 = float(np.clip(lo_hz / nyq, 0.002, 0.90))
    w2 = float(np.clip(hi_hz / nyq, w1 + 0.02, 0.96))
    sos = signal.butter(order, [w1, w2], btype="bandpass", output="sos")
    return signal.sosfilt(sos, x)


def _osc(wave_type: str, phase: np.ndarray, duty: float = 0.5) -> np.ndarray:
    p = phase % 1.0
    if wave_type == "sine":
        return np.sin(2.0 * np.pi * p)
    if wave_type == "tri":
        return 1.0 - 4.0 * np.abs(np.round(p - 0.25) - (p - 0.25))
    if wave_type == "saw":
        return 2.0 * p - 1.0
    if wave_type == "square":
        return np.where(p < duty, 1.0, -1.0)
    raise ValueError(wave_type)


def _env(n: int, atk_ms: float, dec_curve: float = 2.0) -> np.ndarray:
    atk_n = min(n // 2, max(1, int(SR * atk_ms / 1000.0)))
    e = np.ones(n, dtype=np.float64)
    e[:atk_n] = np.linspace(0.0, 1.0, atk_n)
    tail_n = n - atk_n
    if tail_n > 0:
        t = np.linspace(0.0, 1.0, tail_n)
        e[atk_n:] = np.power(np.maximum(0.0, 1.0 - t), dec_curve)
    return e


def _fm_note(freq: float, dur_s: float, ratio: float = 2.41, mod_idx: float = 1.6, dec: float = 3.2, rng: np.random.Generator | None = None) -> np.ndarray:
    n = max(512, int(SR * dur_s))
    t = np.arange(n, dtype=np.float64) / SR
    mod_env = np.exp(-t * (6.0 / max(0.04, dur_s)))
    mod = np.sin(2.0 * np.pi * freq * ratio * t) * mod_idx * mod_env
    sig = np.sin(2.0 * np.pi * freq * t + mod) * _env(n, 2.0, dec)
    if rng is not None:
        sig += (rng.standard_normal(n) * 0.015) * np.exp(-t * 45.0)
    return sig


def _add_echo(x: np.ndarray, delay_ms: float = 48.0, mix: float = 0.22, taps: int = 2) -> np.ndarray:
    d = int(SR * delay_ms / 1000.0)
    pad = d * taps + 256
    out = np.zeros(len(x) + pad, dtype=np.float64)
    out[:len(x)] = x
    for k in range(1, taps + 1):
        gain = mix * (0.55 ** (k - 1))
        off = d * k
        out[off:off + len(x)] += x * gain
    return out


def _seq_notes(freqs: list[float], step_s: float, tail_s: float, mode: str = "fm", duty: float = 0.45) -> np.ndarray:
    step_n = int(SR * step_s)
    note_n = int(SR * (step_s + tail_s))
    total = step_n * (len(freqs) - 1) + note_n
    out = np.zeros(total, dtype=np.float64)
    for idx, f in enumerate(freqs):
        start = idx * step_n
        if mode == "fm":
            seg = _fm_note(f, step_s + tail_s, ratio=2.0 + 0.12 * (idx % 3), mod_idx=1.4, dec=2.4)
        else:
            t = np.arange(note_n, dtype=np.float64) / SR
            ph = np.cumsum(np.full(note_n, f / SR))
            seg = _osc(mode, ph, duty=duty) * _env(note_n, 2.5, 1.9)
            seg = _butter_filter(seg, "lowpass", min(14000.0, f * 6.5))
        out[start:start + len(seg)] += seg
    return out


def _master(x: np.ndarray, target_peak: float = 0.89) -> np.ndarray:
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = _butter_filter(x, "highpass", 35.0, order=1)
    # Trim ultra-quiet tail
    nz = np.where(np.abs(x) > 0.0012)[0]
    if len(nz) > 0:
        end = min(len(x), int(nz[-1]) + int(SR * 0.015))
        x = x[:max(int(SR * 0.04), end)]
    x = np.tanh(x * 1.2)
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    if peak > 1e-6:
        x = x * (target_peak / peak)
    # Anti-click micro fades
    fi = min(len(x) // 4, int(SR * 0.003))
    fo = min(len(x) // 3, int(SR * 0.008))
    if fi > 1:
        x[:fi] *= np.linspace(0.0, 1.0, fi)
    if fo > 1:
        x[-fo:] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, fo)))
    return x


def synth_sound(cat_idx: int, item_idx: int) -> np.ndarray:
    seed = 9001 + cat_idx * 131 + item_idx * 37
    rng = np.random.default_rng(seed)
    u = item_idx / 14.0  # 0..1 spread inside category

    if cat_idx == 0:  # UI Clicks
        dur = 0.042 + 0.045 * (item_idx % 5) / 4.0
        n = int(SR * dur)
        t = np.arange(n) / SR
        f0 = 700 + item_idx * 135
        f1 = f0 * (0.28 + 0.35 * ((item_idx + 2) % 3) / 2.0)
        freqs = f0 + (f1 - f0) * np.power(t / dur, 0.45)
        ph = np.cumsum(freqs / SR)
        wave_kind = ["tri", "sine", "square", "tri", "saw"][item_idx % 5]
        sig = _osc(wave_kind, ph, 0.35) * _env(n, 0.8, 3.2)
        click_noise = _bandpass(rng.standard_normal(n), 1800 + u * 2500, 6500 + u * 3000) * np.exp(-t * 140.0) * 0.55
        out = _butter_filter(sig + click_noise, "lowpass", 4200 + u * 6800)
        return _master(out, 0.84)

    if cat_idx == 1:  # UI Confirm & Success
        base_scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
        root = base_scale[item_idx % len(base_scale)] * (1.0 if item_idx < 8 else 1.122)
        intervals = [[1, 1.5], [1, 1.25, 1.5], [1, 1.25, 1.5, 2.0], [1, 1.5, 2.0]][item_idx % 4]
        freqs = [root * r for r in intervals]
        mode = "fm" if item_idx % 3 != 2 else "tri"
        out = _seq_notes(freqs, 0.055 + 0.015 * (item_idx % 3), 0.24 + 0.06 * (item_idx % 2), mode=mode)
        return _master(_add_echo(out, 52.0, 0.22, 2), 0.88)

    if cat_idx == 2:  # UI Alerts & Errors
        root = 180 + (item_idx % 5) * 35
        if item_idx % 3 == 0:
            freqs = [root * 1.18, root * 0.88]
            out = _seq_notes(freqs, 0.085, 0.14, mode="saw")
        elif item_idx % 3 == 1:
            n = int(SR * (0.22 + 0.03 * (item_idx % 4)))
            t = np.arange(n) / SR
            vib = 1.0 + 0.06 * np.sin(2.0 * np.pi * (28 + item_idx * 2) * t)
            ph = np.cumsum((root * vib * np.linspace(1.0, 0.72, n)) / SR)
            out = _osc("square", ph, 0.42) * _env(n, 2.0, 1.8)
        else:
            freqs = [root * 1.4, root * 1.0, root * 0.7]
            out = _seq_notes(freqs, 0.06, 0.11, mode="square", duty=0.35)
        out = _butter_filter(out, "lowpass", 2400 + u * 1800)
        return _master(out, 0.86)

    if cat_idx == 3:  # Coins, Pickups & Gems
        roots = [784, 880, 987.77, 1046.5, 1174.66]
        r = roots[item_idx % len(roots)]
        if item_idx < 5:
            out = _seq_notes([r, r * 1.3348], 0.068, 0.22, mode="square", duty=0.45)
        elif item_idx < 10:
            out = _seq_notes([r, r * 1.25, r * 1.5, r * 2.0], 0.048, 0.24, mode="fm")
        else:
            out = _seq_notes([r * 0.85, r * 1.12, r * 1.5], 0.055, 0.28, mode="fm")
        return _master(_add_echo(out, 42.0, 0.20, 2), 0.89)

    if cat_idx == 4:  # Jumps, Hops & Movement
        dur = 0.14 + 0.025 * (item_idx % 5)
        n = int(SR * dur)
        t = np.arange(n) / SR
        if item_idx in (5, 6, 10, 11):  # Lands / Steps / Thuds
            f_start = 240 + item_idx * 18
            f_end = 55 + (item_idx % 3) * 15
            ph = np.cumsum((f_start + (f_end - f_start) * np.power(t / dur, 0.45)) / SR)
            sig = _osc("sine", ph) * _env(n, 1.5, 2.6)
            grit = _bandpass(rng.standard_normal(n), 200, 1400) * np.exp(-t * 32.0) * 0.45
            return _master(sig + grit, 0.9)
        f_start = 190 + item_idx * 24
        f_end = f_start * (2.1 + 0.25 * (item_idx % 4))
        ph = np.cumsum((f_start + (f_end - f_start) * np.power(t / dur, 0.72)) / SR)
        wk = "square" if item_idx % 2 == 0 else "tri"
        sig = _osc(wk, ph, 0.38) * _env(n, 3.0, 1.7)
        if item_idx in (3, 13, 14):  # Dash / Jet / Teleport
            sig += _bandpass(rng.standard_normal(n), 600, 4200) * _env(n, 5.0, 2.2) * 0.45
        return _master(_butter_filter(sig, "lowpass", 7500), 0.88)

    if cat_idx == 5:  # Lasers, Blasters & Sci-Fi
        dur = 0.16 + 0.03 * (item_idx % 6)
        n = int(SR * dur)
        t = np.arange(n) / SR
        f0 = 1100 + item_idx * 140
        f1 = 130 + (item_idx % 4) * 45
        sweep = f0 * np.power(f1 / f0, np.power(t / dur, 0.55))
        if item_idx % 4 == 3:
            sweep *= 1.0 + 0.12 * np.sin(2.0 * np.pi * 42.0 * t)
        ph = np.cumsum(sweep / SR)
        wk = ["saw", "square", "saw", "fm"][item_idx % 4]
        sig = _osc("saw" if wk == "fm" else wk, ph, 0.45) * _env(n, 1.5, 1.8)
        if wk == "fm":
            sig += np.sin(2.0 * np.pi * ph + 2.5 * np.sin(2.0 * np.pi * ph * 1.73)) * _env(n, 1.5, 2.0) * 0.6
        out = _butter_filter(sig, "lowpass", 10500)
        return _master(_add_echo(out, 36.0, 0.16, 2), 0.89)

    if cat_idx == 6:  # Impacts, Hits & Punches
        dur = 0.15 + 0.035 * (item_idx % 5)
        n = int(SR * dur)
        t = np.arange(n) / SR
        if item_idx in (3, 8):  # Shield clang / Parry metallic ring
            ring = (_fm_note(620 + item_idx * 40, dur, 2.73, 3.2, 2.6) + _fm_note(980 + item_idx * 55, dur, 1.91, 2.4, 3.0) * 0.6)
            transient = _bandpass(rng.standard_normal(n), 1500, 6000) * np.exp(-t * 95.0) * 0.7
            return _master(ring + transient, 0.9)
        f0 = 240 + (item_idx % 5) * 45
        sweep = f0 * np.power(45.0 / f0, np.power(t / dur, 0.4))
        body = np.sin(2.0 * np.pi * np.cumsum(sweep / SR)) * np.exp(-t * 22.0)
        noise_cut = 1800 + item_idx * 320
        crunch = _butter_filter(rng.standard_normal(n), "lowpass", noise_cut) * np.exp(-t * 28.0) * 0.85
        return _master(body * 1.2 + crunch, 0.92)

    if cat_idx == 7:  # Explosions & Booms
        dur = 0.48 + 0.08 * (item_idx % 6)
        n = int(SR * dur)
        t = np.arange(n) / SR
        raw_n = rng.standard_normal(n)
        # Bit-crushed stepped crunch on some retro variants
        if item_idx % 3 == 1:
            hold = max(2, 4 + (item_idx % 4) * 3)
            raw_n = np.repeat(raw_n[::hold], hold)[:n]
        cutoff = 650 + 2600 * np.exp(-t * (3.2 + 0.4 * (item_idx % 4)))
        low = _butter_filter(raw_n, "lowpass", 420 + (item_idx % 5) * 85) * np.exp(-t * 3.8) * 1.3
        mid = _bandpass(raw_n, 280, 1800 + item_idx * 90) * np.exp(-t * 6.5) * 0.75
        sub_sweep = 115 * np.power(28.0 / 115.0, np.power(t / dur, 0.35))
        sub = np.sin(2.0 * np.pi * np.cumsum(sub_sweep / SR)) * np.exp(-t * 4.5) * 1.1
        out = _add_echo(low + mid + sub, 64.0, 0.24, 2)
        return _master(out, 0.93)

    if cat_idx == 8:  # Powerups & Level Up
        roots = [392.0, 440.0, 523.25, 587.33, 659.25]
        r = roots[item_idx % len(roots)]
        patterns = [
            [1, 1.25, 1.5, 2.0],
            [1, 1.189, 1.498, 2.0, 2.5],
            [1, 1.5, 1.875, 2.0],
            [1, 1.122, 1.25, 1.5, 2.0],
        ]
        freqs = [r * p for p in patterns[item_idx % len(patterns)]]
        mode = ["tri", "fm", "square", "fm"][item_idx % 4]
        out = _seq_notes(freqs, 0.062 + 0.01 * (item_idx % 3), 0.30, mode=mode, duty=0.4)
        return _master(_add_echo(out, 55.0, 0.25, 3), 0.89)

    # cat_idx == 9: Menus, Swooshes & Transitions
    dur = 0.18 + 0.04 * (item_idx % 6)
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    center = 700 + item_idx * 180
    if item_idx % 3 == 0:
        band = _bandpass(noise, max(160, center * 0.4), min(9000, center * 2.2))
        env = np.sin(np.pi * (t / dur)) ** 1.3
        out = band * env
    elif item_idx % 3 == 1:
        # Pop + air tail
        f_sw = 260 + item_idx * 40 + (340 * np.power(t / dur, 0.5))
        tone = np.sin(2.0 * np.pi * np.cumsum(f_sw / SR)) * np.exp(-t * 16.0) * 0.7
        air = _bandpass(noise, 900, 4800) * np.exp(-t * 14.0) * 0.55
        out = tone + air
    else:
        # Shimmer transition
        ch = _fm_note(520 + item_idx * 38, dur, 2.0, 1.1, 1.8)
        air = _bandpass(noise, 1400, 6200) * (np.sin(np.pi * (t / dur)) ** 1.6) * 0.45
        out = ch + air
    return _master(_add_echo(out, 46.0, 0.20, 2), 0.86)


def write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(samples, -1.0, 1.0)
    int16 = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int16.tobytes())


def encode_ogg(pair: tuple[Path, Path]) -> None:
    wav_p, ogg_p = pair
    ogg_p.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(wav_p), "-c:a", "libopus", "-b:a", "128k", str(ogg_p)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg OGG encode failed for {wav_p}: {res.stderr}")


def _load_font(size: int, mono: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    candidates = (
        [
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Monaco.ttf",
            "/Library/Fonts/Courier New.ttf",
        ]
        if mono
        else [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNS.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    )
    for fp in candidates:
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_preview_sheet(records: list[dict[str, Any]], waveforms: dict[str, np.ndarray], out_png: Path) -> None:
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), "#0b0f14")
    draw = ImageDraw.Draw(img)

    f_title = _load_font(34)
    f_sub = _load_font(17)
    f_card = _load_font(16)
    f_mono = _load_font(13, mono=True)

    # Header bar
    draw.rectangle([0, 0, W, 94], fill="#131922")
    draw.line([0, 94, W, 94], fill="#283548", width=2)
    draw.text((34, 18), "150 CC0 UI & ARCADE SFX MEGA-PACK", fill="#f8fafc", font=f_title)
    draw.text((34, 60), "10 Folders x 15 Studio-Mastered Sounds  |  44.1kHz 16-Bit WAV + OGG  |  100% Pure DSP (Zero AI)", fill="#94a3b8", font=f_sub)

    # Right header pill
    draw.rounded_rectangle([995, 22, 1246, 72], radius=10, fill="#f59e0b")
    draw.text(((995 + 1246) // 2, (22 + 72) // 2), "CC0 · 300 FILES", fill="#0b0f14", font=f_card, anchor="mm")

    # 2x5 grid of category waveform cards
    cols, rows = 2, 5
    margin_x, margin_y = 34, 112
    gap_x, gap_y = 22, 12
    card_w = (W - margin_x * 2 - gap_x) // cols
    card_h = (H - margin_y - 44 - gap_y * (rows - 1)) // rows

    for idx, (folder, label, _names) in enumerate(CATEGORIES):
        c = idx % cols
        r = idx // cols
        x0 = margin_x + c * (card_w + gap_x)
        y0 = margin_y + r * (card_h + gap_y)
        x1 = x0 + card_w
        y1 = y0 + card_h

        draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill="#131922", outline="#283548", width=1)
        draw.text((x0 + 16, y0 + 14), f"{idx + 1:02d}. {label}", fill="#f1f5f9", font=f_card)
        draw.text((x0 + 16, y0 + 40), f"{folder}/", fill="#38bdf8", font=f_mono)
        draw.text((x0 + 16, y0 + 62), "15 WAV + 15 OGG", fill="#94a3b8", font=f_mono)

        # Mini waveform preview box on right half of card
        wx0, wy0, wx1, wy1 = x0 + 318, y0 + 14, x1 - 16, y1 - 14
        draw.rounded_rectangle([wx0, wy0, wx1, wy1], radius=6, fill="#05080c", outline="#1e293b", width=1)
        mid_y = (wy0 + wy1) // 2
        draw.line([wx0 + 4, mid_y, wx1 - 4, mid_y], fill="#1e293b", width=1)

        samples = waveforms[folder]
        span = wx1 - wx0 - 12
        half_h = (wy1 - wy0 - 12) // 2
        pts = []
        for px in range(span):
            s_i = int((px / max(1, span - 1)) * (len(samples) - 1))
            s_j = min(len(samples), s_i + max(1, len(samples) // span))
            val = float(np.max(np.abs(samples[s_i:s_j]))) if s_j > s_i else abs(float(samples[s_i]))
            x_px = wx0 + 6 + px
            pts.append((x_px, int(mid_y - val * half_h)))
        for k in range(len(pts) - 1):
            x_a, y_a = pts[k]
            draw.line([x_a, y_a, x_a, mid_y + (mid_y - y_a)], fill="#f59e0b" if idx % 2 == 0 else "#38bdf8", width=1)

    draw.text((34, H - 24), "Each-Touch Asset Lab  ·  Free 20-SFX Demo Included  ·  Commercial-Safe CC0 1.0", fill="#8b9bb4", font=f_mono)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, "PNG")


def main() -> int:
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    if SAMPLES_DIR.exists():
        shutil.rmtree(SAMPLES_DIR)
    WAV_DIR.mkdir(parents=True, exist_ok=True)
    OGG_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    SS_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    ogg_jobs: list[tuple[Path, Path]] = []
    rep_waveforms: dict[str, np.ndarray] = {}
    demo_entries: list[tuple[str, Path, Path]] = []

    for cat_idx, (folder, cat_label, names) in enumerate(CATEGORIES):
        for item_idx, item_name in enumerate(names):
            samples = synth_sound(cat_idx, item_idx)
            peak = float(np.max(np.abs(samples)))
            rms = float(np.sqrt(np.mean(samples ** 2)))
            dur_ms = round((len(samples) / SR) * 1000.0, 1)
            assert not np.any(np.isnan(samples)), f"NaN in {folder}/{item_name}"
            assert 0.15 < peak <= 0.99, f"Bad peak {peak} in {folder}/{item_name}"
            assert 35 <= dur_ms <= 2500, f"Bad duration {dur_ms}ms in {folder}/{item_name}"

            fname = f"{item_idx + 1:02d}_{item_name}"
            wav_p = WAV_DIR / folder / f"{fname}.wav"
            ogg_p = OGG_DIR / folder / f"{fname}.ogg"
            write_wav(wav_p, samples)
            ogg_jobs.append((wav_p, ogg_p))

            is_demo = item_idx in (0, 2)
            if item_idx == 0:
                rep_waveforms[folder] = samples

            records.append({
                "id": len(records) + 1,
                "folder": folder,
                "category": cat_label,
                "name": item_name,
                "wav": f"WAV/{folder}/{fname}.wav",
                "ogg": f"OGG/{folder}/{fname}.ogg",
                "durationMs": dur_ms,
                "peakDbfs": round(20.0 * math.log10(peak), 2),
                "rmsDbfs": round(20.0 * math.log10(max(1e-6, rms)), 2),
                "inDemo": is_demo,
            })
            if is_demo:
                demo_entries.append((f"{folder}/{fname}", wav_p, ogg_p))

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(encode_ogg, ogg_jobs))

    # Copy 1 representative MP3 per category to web audition samples (universal browser support)
    web_samples = []
    for cat_idx, (folder, cat_label, names) in enumerate(CATEGORIES):
        src_wav = WAV_DIR / folder / f"01_{names[0]}.wav"
        dst_name = f"{folder}_01_{names[0]}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src_wav), "-c:a", "libmp3lame", "-q:a", "2", str(SAMPLES_DIR / dst_name)],
            check=True,
        )
        web_samples.append({
            "folder": folder,
            "category": cat_label,
            "sampleFile": f"samples/{dst_name}",
            "sampleTitle": names[0].replace("_", " ").title(),
            "count": len(names),
        })

    DOCS_PACK_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_PACK_DIR / "manifest.json").write_text(
        json.dumps({"slug": SLUG, "total": len(records), "categories": web_samples, "tracklist": records}, indent=2),
        encoding="utf-8",
    )

    # Preview sheet PNG
    render_preview_sheet(records, rep_waveforms, REL_DIR / "preview_sheet_1280x720.png")

    # Build Paid Full Pack ZIP (gitignored!)
    full_zip = REL_DIR / "each-touch-150-ui-game-sfx-full-cc0.zip"
    csv_lines = ["id,category,folder,filename,duration_ms,peak_dbfs,rms_dbfs,wav_path,ogg_path"]
    for rec in records:
        csv_lines.append(
            f"{rec['id']},{rec['category']},{rec['folder']},{rec['name']},{rec['durationMs']},{rec['peakDbfs']},{rec['rmsDbfs']},{rec['wav']},{rec['ogg']}"
        )

    with zipfile.ZipFile(full_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rec in records:
            wav_src = WORK_DIR / rec["wav"].replace("WAV/", "wav/", 1)
            ogg_src = WORK_DIR / rec["ogg"].replace("OGG/", "ogg/", 1)
            zf.write(wav_src, arcname=rec["wav"])
            zf.write(ogg_src, arcname=rec["ogg"])
        zf.writestr("LICENSE-CC0.txt", CC0_LICENSE.encode("utf-8"))
        zf.writestr("TRACKLIST.csv", "\n".join(csv_lines).encode("utf-8"))
        zf.writestr("manifest.json", json.dumps({"pack": SLUG, "license": "CC0-1.0", "zeroAI": True, "files": records}, indent=2).encode("utf-8"))

    # Build Free 20-SFX Demo ZIP
    demo_zip = REL_DIR / "each-touch-20-ui-game-sfx-free-demo-cc0.zip"
    with zipfile.ZipFile(demo_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_name, wav_src, ogg_src in demo_entries:
            zf.write(wav_src, arcname=f"WAV/{rel_name}.wav")
            zf.write(ogg_src, arcname=f"OGG/{rel_name}.ogg")
        zf.writestr("LICENSE-CC0.txt", CC0_LICENSE.encode("utf-8"))
        zf.writestr("UPGRADE_TO_150_FULL_PACK.txt", UPGRADE_NOTE.encode("utf-8"))

    # Integrity verify
    with zipfile.ZipFile(full_zip, "r") as zf:
        assert zf.testzip() is None
        audio_cnt = sum(1 for n in zf.namelist() if n.endswith((".wav", ".ogg")))
        assert audio_cnt == 300, f"Expected 300 audio files, got {audio_cnt}"
    with zipfile.ZipFile(demo_zip, "r") as zf:
        assert zf.testzip() is None
        demo_cnt = sum(1 for n in zf.namelist() if n.endswith((".wav", ".ogg")))
        assert demo_cnt == 40, f"Expected 40 demo audio files, got {demo_cnt}"

    shutil.rmtree(WORK_DIR)
    print(f"Generated 150 SFX Full Pack ({full_zip.stat().st_size} bytes, 300 audio) & 20 SFX Demo ({demo_zip.stat().st_size} bytes, 40 audio)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
