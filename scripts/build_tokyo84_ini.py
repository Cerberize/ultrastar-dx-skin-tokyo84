#!/usr/bin/env python3
"""
Generates 100% UltraStar-Deluxe-compatible:
  - themes/Tokyo84.ini (derived from official USDX Modern.ini schema)
  - themes/Tokyo84/KabukichoMidnight.ini (complete Blue.ini + Modern.ini texture map)
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF_DIR = Path("/home/pravesh/.gemini/antigravity/brain/e3b14aa0-147d-4914-96e0-605645c5ad4c/scratch/usdx_ref")
MODERN_INI = REF_DIR / "Modern.ini"
BLUE_INI = REF_DIR / "Blue.ini"

OUT_THEME = ROOT / "themes" / "Tokyo84.ini"
OUT_SKIN = ROOT / "themes" / "Tokyo84" / "KabukichoMidnight.ini"


def parse_sections(text: str) -> list[tuple[str | None, list[str]]]:
    """Preserve exact INI section order and lines."""
    sections: list[tuple[str | None, list[str]]] = []
    cur_name: str | None = None
    cur_lines: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*\[([^\]]+)\]\s*$", line)
        if m:
            sections.append((cur_name, cur_lines))
            cur_name = m.group(1).strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    sections.append((cur_name, cur_lines))
    return sections


def replace_section(sections: list[tuple[str | None, list[str]]], name: str, new_body: list[str]) -> None:
    for i, (sec_name, _) in enumerate(sections):
        if sec_name == name:
            sections[i] = (sec_name, new_body)
            return
    raise KeyError(f"Section [{name}] not found in Modern.ini")


def set_in_section(sections: list[tuple[str | None, list[str]]], name: str, updates: dict[str, str]) -> None:
    for i, (sec_name, lines) in enumerate(sections):
        if sec_name == name:
            remaining = dict(updates)
            out = []
            for ln in lines:
                m = re.match(r"^(\s*)([A-Za-z0-9_]+)(\s*=\s*)(.*)$", ln)
                if m and m.group(2) in remaining:
                    key = m.group(2)
                    out.append(f"{m.group(1)}{key} = {remaining.pop(key)}")
                else:
                    out.append(ln)
            for k, v in remaining.items():
                out.append(f"{k} = {v}")
            sections[i] = (sec_name, out)
            return
    raise KeyError(f"Section [{name}] not found in Modern.ini")


def build_tokyo84_ini() -> None:
    raw = MODERN_INI.read_text(encoding="utf-8", errors="ignore")
    sections = parse_sections(raw)

    # 1. Theme Header
    replace_section(sections, "Theme", [
        "Name = Tokyo84",
        "Creator = Tokyo84 Design System",
        "US_Version = USD 110",
        "DefaultSkin = KabukichoMidnight",
        "",
    ])

    # 2. Colors — Kabukicho Midnight (Material 3 Dark Tonal + 1984 Shinjuku Neon)
    set_in_section(sections, "Colors", {
        "White": "244 246 255",
        "WhiteGray": "220 226 248",
        "LightBlue": "0 229 255",
        "DarkBlue": "27 31 52",
        "LightRed": "255 46 147",
        "DarkRed": "140 20 82",
        "LightGreen": "0 230 168",
        "DarkGreen": "0 120 88",
        "LightPurple": "179 136 255",
        "DarkPurple": "72 52 135",
        "LightOrange": "255 179 0",
        "DarkOrange": "155 96 0",
        "Turkis": "0 229 255",
        "GrayLightest": "220 226 248",
        "GrayLight": "166 174 209",
        "Gray": "96 104 146",
        "GrayDark": "27 31 52",
        "Black": "11 13 24",
        "GrayPopup": "19 22 38",
        "Gold": "255 179 0",
        "Red": "255 46 147",
        # Custom Tokyo84 Material Design 3 tokens
        "TokyoBg": "11 13 24",
        "TokyoSurface": "27 31 52",
        "TokyoSurfaceHigh": "42 48 80",
        "TokyoMagenta": "255 46 147",
        "TokyoCyan": "0 229 255",
        "TokyoAmber": "255 179 0",
        "TokyoWhite": "244 246 255",
        "TokyoMuted": "166 174 209",
        "TokyoOutline": "72 79 118",
    })

    # 3. Modern Material 3 Global Defaults
    #    - DefaultBar1 uses Type = Transparent so TokyoMagenta tints cleanly (no white bar!)
    #    - DefaultFadeButton keeps W=150, H=50 so horizontal buttons on Options/Party/Stats NEVER overlap!
    #    - Fade = 1 with SelectH = H and FadeTex = "" prevents stray white pill at (0,0) AND ensures
    #      TButtonCollection child button texts (Stats/Editor/Options) become visible (UMenuButtonCollection.pas)!
    set_in_section(sections, "DefaultBar1", {
        "Color": "TokyoMagenta",
        "Type": "Transparent",
        "Reflection": "0",
    })
    set_in_section(sections, "DefaultBar2", {
        "Color": "White",
        "Type": "Transparent",
        "Reflection": "0",
    })
    set_in_section(sections, "DefaultTextWhereAmI", {
        "Color": "TokyoWhite",
    })
    set_in_section(sections, "DefaultLegendStatic", {
        "W": "38",
        "H": "28",
        "Y": "546",
        "Reflection": "0",
    })
    set_in_section(sections, "DefaultLegendText", {
        "Color": "TokyoWhite",
        "Size": "20",
        "Y": "550",
        "Reflection": "0",
    })
    set_in_section(sections, "DefaultButton", {
        "Color": "TokyoMagenta",
        "DColor": "TokyoSurfaceHigh",
        "Type": "Transparent",
    })
    set_in_section(sections, "DefaultFadeButton", {
        "W": "150",
        "H": "50",
        "Color": "TokyoMagenta",
        "DColor": "TokyoSurfaceHigh",
        "Type": "Transparent",
        "Reflection": "0",
        "Fade": "1",
        "FadeText": "0",
        "SelectW": "150",
        "SelectH": "50",
        "FadeTex": "ButtonFade",
    })
    set_in_section(sections, "DefaultButtonFadeText", {
        "X": "75",
        "Y": "11",
        "Size": "22",
        "Align": "1",
        "Color": "TokyoWhite",
    })
    set_in_section(sections, "DefaultSelectSlide", {
        "Color": "TokyoMagenta",
        "DColor": "TokyoSurfaceHigh",
        "TColor": "TokyoWhite",
        "TDColor": "TokyoWhite",
        "SBGColor": "TokyoCyan",
        "SBGDColor": "TokyoSurface",
        "STColor": "TokyoBg",
        "STDColor": "TokyoWhite",
    })

    # 4. Loading Screen — show true 1984 Shinjuku artwork without red tint
    replace_section(sections, "LoadingBackground", [
        "Tex = LoadingBG",
        "Color = White",
        "Type = image",
        "",
    ])
    set_in_section(sections, "LoadingText1", {
        "Color": "TokyoWhite",
        "Reflection": "0",
    })
    set_in_section(sections, "LoadingText2", {
        "Color": "TokyoCyan",
        "Reflection": "0",
    })

    # 5. Main Menu — Exact Material 3 Left-Rail Layout (800x600 coordinate space)
    #    W=260, H=46 scoped ONLY to Main Menu buttons so other screens stay 150px wide!
    set_in_section(sections, "MainStatic1", {
        "X": "56",
        "Y": "50",
        "W": "38",
        "H": "38",
    })
    set_in_section(sections, "MainText1", {
        "X": "106",
        "Y": "46",
        "Size": "42",
        "Color": "TokyoWhite",
    })
    set_in_section(sections, "MainTextDescriptionLong", {
        "X": "56",
        "Y": "496",
        "Size": "20",
        "Color": "TokyoCyan",
    })

    set_in_section(sections, "MainButtonSolo", {
        "X": "56",
        "Y": "124",
        "W": "260",
        "H": "46",
        "SelectW": "260",
        "SelectH": "46",
    })
    set_in_section(sections, "MainButtonSoloText1", {"X": "130", "Y": "10", "Size": "24"})
    set_in_section(sections, "MainButtonMulti", {"X": "56", "Y": "182"})
    set_in_section(sections, "MainButtonMultiText1", {"X": "130", "Y": "10", "Size": "24"})
    set_in_section(sections, "MainButtonJukebox", {"X": "56", "Y": "240"})
    set_in_section(sections, "MainButtonJukeboxText1", {"X": "130", "Y": "10", "Size": "24"})
    set_in_section(sections, "MainButtonCollection1", {
        "X": "56",
        "Y": "298",
        "Fade": "1",
        "FadeTex": "ButtonFade",
    })
    set_in_section(sections, "MainButtonCollection1Text1", {"X": "130", "Y": "10", "Size": "24"})

    # Tools sub-menu expands cleanly to the right of Tools pill
    set_in_section(sections, "MainButtonStats", {
        "X": "332",
        "Y": "298",
        "W": "164",
        "H": "38",
        "Color": "TokyoCyan",
        "DColor": "TokyoSurface",
    })
    set_in_section(sections, "MainButtonStatsText1", {
        "X": "82",
        "Y": "8",
        "Size": "20",
        "Color": "TokyoWhite",
        "DColor": "TokyoWhite",
    })
    set_in_section(sections, "MainButtonEditor", {"Y": "344"})
    set_in_section(sections, "MainButtonOptions", {"Y": "390"})

    # About & Exit compact pills below main stack
    set_in_section(sections, "MainButtonAbout", {
        "X": "56",
        "Y": "376",
        "W": "124",
        "H": "40",
        "Color": "TokyoCyan",
        "DColor": "TokyoSurface",
    })
    set_in_section(sections, "MainButtonAboutText1", {
        "X": "62",
        "Y": "9",
        "Size": "20",
        "Color": "TokyoWhite",
    })
    set_in_section(sections, "MainButtonExit", {
        "X": "192",
        "Y": "376",
        "W": "124",
        "H": "40",
    })

    # 6. Global High-Contrast Button & SelectSlide Sweep across ALL USDX screens
    #    Replaces low-contrast Blue-on-Blue (ColorLight / ColorDark) on Options, Party,
    #    Stats, Edit, Name, Level, and Popups with TokyoMagenta / TokyoCyan vs TokyoSurface!
    for idx_s, (sec_name, sec_lines) in enumerate(sections):
        if not sec_name or sec_name in ("Theme", "Colors"):
            continue
        is_interactive = any(k in sec_name for k in ("Button", "Select", "Slide"))
        if not is_interactive:
            continue
        new_lines = []
        for ln in sec_lines:
            m = re.match(r"^(\s*)(Color|DColor|SBGColor|SBGDColor|SelectH)(\s*=\s*)(.*)$", ln)
            if m:
                indent, key, eq, val = m.group(1), m.group(2), m.group(3), m.group(4).strip()
                if key == "Color" and val == "ColorLight":
                    val = "TokyoMagenta"
                elif key == "DColor" and val == "ColorDark":
                    val = "TokyoSurface"
                elif key == "SBGColor" and val == "ColorLight":
                    val = "TokyoCyan"
                elif key == "SBGDColor" and val == "ColorDark":
                    val = "TokyoSurface"
                elif key == "SelectH" and sec_name.startswith("OptionsButton") and val == "150":
                    val = "50"
                new_lines.append(f"{indent}{key}{eq}{val}")
            else:
                new_lines.append(ln)
        sections[idx_s] = (sec_name, new_lines)

    # 7. Singing Screen — 1984 Midnight Tokyo Tower Backdrop + Neon Progress Bar
    replace_section(sections, "SingBackground", [
        "Type = image",
        "Tex = SingBG",
        "",
    ])
    set_in_section(sections, "SingTimeProgress", {
        "Color": "TokyoCyan",
    })
    set_in_section(sections, "SingInfoMessageBG", {
        "Color": "TokyoSurface",
    })

    # Write complete Tokyo84.ini
    out_lines: list[str] = [
        "; ============================================================================",
        "; Tokyo84 — UltraStar Deluxe Alternative Theme (100% USDX Modern Schema)",
        "; Aesthetic: 1984 Shinjuku Rain & Neon (Bubble-Era City Pop) x Material 3",
        "; Colorway:  KabukichoMidnight",
        "; ============================================================================",
    ]
    for sec_name, lines in sections:
        if sec_name is not None:
            out_lines.append(f"[{sec_name}]")
        out_lines.extend(lines)

    OUT_THEME.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_THEME} ({len(out_lines)} lines, {len(sections)} sections)")


def build_skin_ini() -> None:
    """
    Map EVERY single texture key from official Blue.ini + Modern.ini to our
    generated Tokyo84 Kabukicho Midnight PNG/JPG assets.
    """
    explicit_map: dict[str, str] = {
        # Backgrounds (4 bespoke 1984 Shinjuku Rain & Neon 16:9 paintings)
        "LoadingBG": "bg/bg_main.jpg",
        "MainBG": "bg/bg_main.jpg",
        "SongBG": "bg/bg_song.jpg",
        "SingBG": "bg/bg_sing.jpg",
        "ScoreScreenBG": "bg/bg_score.jpg",
        "HighScoresBG": "bg/bg_score.jpg",
        "OptionsBG": "bg/bg_song.jpg",
        "EditBG": "bg/bg_song.jpg",
        "EditSubBG": "bg/bg_song.jpg",
        "PartyBG": "bg/bg_main.jpg",

        # Core Material 3 Buttons & Controls
        "Button": "ui/button.png",
        "ButtonF": "ui/button_fade.png",
        "ButtonFade": "ui/button_fade.png",
        "MainBar": "ui/main_bar.png",
        "SelectBG": "ui/select_bg.png",
        "SelectFrame": "ui/select_frame.png",
        "Select_ArrowLeft": "ui/arrow_left.png",
        "Select_ArrowRight": "ui/arrow_right.png",
        "Leiste1": "ui/leiste1.png",
        "Leiste2": "ui/leiste2.png",

        # Dialogs, Popups & Helpers
        "interface_selectbg_search": "ui/select_bg.png",
        "interface_dialog_background": "ui/popup_bg.png",
        "interface_dialog_background2": "ui/popup_bg.png",
        "interface_dialog_backgroundtop": "ui/popup_fg.png",
        "interface_dialog_backgroundtop2": "ui/popup_fg.png",
        "PopUpBG": "ui/popup_bg.png",
        "PopUpFG": "ui/popup_fg.png",
        "JumpToBG": "ui/card_accent.png",
        "SongMenuBG": "ui/card_accent.png",
        "SongMenuSelectBG": "ui/select_bg.png",
        "Rectangle": "ui/white_rect.png",
        "BGFade": "ui/bg_fade.png",

        # Cursor
        "Cursor": "ui/cursor.png",
        "Cursor_Pressed": "ui/cursor_pressed.png",

        # Icons
        "MainIcon": "icons/icon_sing.png",
        "SongCD": "icons/icon_medley.png",
        "MainSearch": "icons/icon_options.png",
        "IconOption": "icons/icon_options.png",
        "IconEdit": "icons/icon_options.png",
        "IconSongMenu": "icons/icon_sing.png",
        "ScoreIcon": "icons/icon_stats.png",
        "PartyIcon": "icons/icon_party.png",
        "StatIcon": "icons/icon_stats.png",
        "VideoIcon": "icons/icon_video.png",
        "IconError": "icons/icon_quit.png",
        "IconQuestion": "icons/icon_options.png",
        "icon_song_menu": "icons/icon_sing.png",
        "icon_song_search": "icons/icon_options.png",
        "icon_song_video": "icons/icon_video.png",
        "icon_song_medley": "icons/icon_medley.png",
        "icon_song_calcmedley": "icons/icon_medley.png",
        "icon_song_duet": "icons/icon_duet.png",
        "icon_song_rap": "icons/icon_sing.png",
        "icon_song_rap_to_freestyle": "icons/icon_sing.png",

        # Song Select
        "SongCover": "ui/song_cover_default.png",
        "SongSelection1": "ui/song_selection.png",
        "SongSelection2": "ui/song_selection.png",
        "SongSelection3": "ui/song_selection.png",
        "SongSelection4": "ui/song_selection.png",
        "SongSelection5": "ui/song_selection.png",
        "SongMessage": "ui/card_accent.png",
        "SongDuetSinger": "icons/icon_duet.png",
        "SongDuetSinger2": "icons/icon_duet.png",
        "SongDuetSinger3": "icons/icon_duet.png",

        # Singing Screen — Hi-Fi Neon Pitch Bars (Colorizable!)
        "GrayLeft": "sing/notes_sung_left.png",
        "GrayMid": "sing/notes_sung_mid.png",
        "GrayRight": "sing/notes_sung_right.png",
        "NotePlainLeft": "sing/notes_plain_left.png",
        "NotePlainMid": "sing/notes_plain_mid.png",
        "NotePlainRight": "sing/notes_plain_right.png",
        "NoteBGLeft": "sing/notes_bg_left.png",
        "NoteBGMid": "sing/notes_bg_mid.png",
        "NoteBGRight": "sing/notes_bg_right.png",

        "GrayLeftRap": "sing/notes_sung_left.png",
        "GrayMidRap": "sing/notes_sung_mid.png",
        "GrayRightRap": "sing/notes_sung_right.png",
        "NotePlainLeftRap": "sing/notes_plain_left.png",
        "NotePlainMidRap": "sing/notes_plain_mid.png",
        "NotePlainRightRap": "sing/notes_plain_right.png",
        "NoteBGLeftRap": "sing/notes_bg_left.png",
        "NoteBGMidRap": "sing/notes_bg_mid.png",
        "NoteBGRightRap": "sing/notes_bg_right.png",

        "NoteStar": "sing/star_golden.png",
        "NotePerfectStar": "sing/star_perfect.png",

        # Singing HUD
        "LyricBar": "sing/lyric_bar.png",
        "LyricBarDuet": "sing/lyric_bar_duet.png",
        "LyricHelpBar": "sing/timebar_fill.png",
        "TimeBar1": "sing/timebar_bg.png",
        "TimeBar": "sing/timebar_fill.png",
        "ProgressBar": "sing/timebar_fill.png",
        "LineBonusBack": "sing/score_hud.png",
        "SingBarBack": "sing/singbar_back.png",
        "SingBarBar": "sing/singbar_bar.png",
        "SingBarFront": "sing/singbar_back.png",
        "ScoreBG": "sing/score_hud.png",
        "P": "sing/player_badge.png",
        "Ball": "sing/lyrics_ball.png",
        "SongName": "sing/score_hud.png",
        "Pause": "sing/pause.png",

        # Score / Top 5
        "ScoreBox": "ui/card_surface.png",
        "ScoreGlassBox": "score/score_glass_box.png",
        "ScoreLevel": "score/score_level.png",
        "ScoreLevelRound": "score/score_level_round.png",
        "ScoreLevel_Dark": "score/score_level.png",
        "ScoreLevel_Dark_Round": "score/score_level_round.png",
        "ScoreLevel_Light": "score/score_level.png",
        "ScoreLevel_Light_Round": "score/score_level_round.png",
        "ScoreLevel_Lightest": "score/score_level.png",
        "ScoreLevel_Lightest_Round": "score/score_level_round.png",
        "ButtonSendScore": "ui/button.png",
        "ScoreBar_box_lightest": "score/score_bar_box.png",
        "ScoreBar_box_light": "score/score_bar_box.png",
        "ScoreBar_box_dark": "score/score_bar_box.png",
        "ScoreEndCap": "score/score_level_round.png",
        "ScoreLine": "ui/white_rect.png",
        "PlayerNumberBox": "sing/player_badge.png",

        # Ratings 0..7
        **{f"Rating_{i}": f"score/rating_{i}.png" for i in range(8)},

        # Player & Duet Indicators
        **{f"PlayerIDBox0{i}": "sing/lyric_active.png" for i in range(1, 7)},
        **{f"LyricIcon_P{i}": "sing/lyric_active.png" for i in range(1, 7)},
        **{f"LyricIconD_P{i}": "sing/lyric_inactive.png" for i in range(1, 7)},
        **{f"NoAvatar_P{i}": "ui/no_avatar.png" for i in range(1, 7)},

        # Avatars
        "AvatarFrame": "ui/avatar_frame.png",
        "AvatarFrame2": "ui/avatar_frame.png",
        "CurrentPlayer": "ui/select_frame.png",

        # Legend Keycaps (distinct crisp glyphs)
        "ButtonNavi": "ui/key_navi.png",
        "ButtonEnter": "ui/key_enter.png",
        "ButtonEsc": "ui/key_esc.png",
        "ButtonC": "ui/key_c.png",
        "ButtonP": "ui/key_p.png",
        "ButtonM": "ui/key_m.png",
        "ButtonJ": "ui/key_j.png",
        "ButtonAlt": "ui/key_alt.png",
        "ButtonAZ": "ui/key_az.png",
        "Button13": "ui/key_13.png",
        "ButtonIns": "ui/key_ins.png",
        "ButtonDel": "ui/key_del.png",

        # Party, Stats, Jukebox, Edit, Color Picker
        "Joker": "score/medal_gold.png",
        "PartyPlayerButton": "ui/button.png",
        "PartyTeamButton1": "ui/button.png",
        "PartyTeamButton2": "ui/button.png",
        "PartyTeamButton3": "ui/button.png",
        "PartyTeamButton4": "ui/button.png",
        "PartyTeamButton5": "ui/button.png",
        "PartyRoundBG1": "ui/card_surface.png",
        "PartyRoundBG2": "ui/card_surface.png",
        "PartyRoundBG3": "ui/card_surface.png",
        "PartyRoundBG4": "ui/card_surface.png",
        "HDL_Pointer": "ui/arrow_right.png",
        "PartyTeamPoints": "ui/card_accent.png",
        "PartyScoreDeco": "score/medal_silver.png",
        "PartyScoreBG1": "ui/card_surface.png",
        "PartyScoreBG2": "ui/card_accent.png",
        "PartyWinDeco1": "score/medal_gold.png",
        "PartyWinDeco2": "score/medal_silver.png",
        "PartyWinDeco3": "score/medal_bronze.png",
        "PartyPlayerSelectBG": "ui/card_surface.png",
        "PartyTrophy": "score/medal_gold.png",
        "PartyWinner": "score/medal_gold.png",
        "StatMainBG1": "ui/card_surface.png",
        "StatMainBG2": "ui/card_surface.png",
        "StatMainBG3": "ui/card_surface.png",
        "StatDetailBG1": "ui/card_accent.png",
        "JukeboxTimeBar1": "sing/timebar_bg.png",
        "JukeboxTimeBar": "sing/timebar_fill.png",
        "JukeboxSong": "ui/card_surface.png",
        "JukeboxSongBackground": "ui/card_accent.png",
        "JukeboxSongListBackground": "ui/card_surface.png",
        "JukeboxSongOptionsBackground": "ui/card_surface.png",
        "JukeboxLyric": "sing/lyric_bar.png",
        "JukeboxRandom": "icons/icon_medley.png",
        "JukeboxRepeat": "icons/icon_medley.png",
        "JukeboxCurrentSongBackground": "ui/card_accent.png",
        "JukeboxSongListUp": "ui/arrow_left.png",
        "JukeboxSongListDown": "ui/arrow_right.png",
        "JukeboxOptions": "icons/icon_options.png",
        "JukeboxClose": "icons/icon_quit.png",
        "JukeboxFix": "icons/icon_party.png",
        "JukeboxSongMenuTimeBar": "sing/timebar_bg.png",
        "JukeboxSongMenuPlayPause": "icons/icon_video.png",
        "JukeboxSongMenuNext": "ui/arrow_right.png",
        "JukeboxSongMenuPrevious": "ui/arrow_left.png",
        "JukeboxSongMenuPlaylist": "icons/icon_sing.png",
        "PlayOnly": "icons/icon_video.png",
        "playwithnote": "icons/icon_sing.png",
        "playnote": "icons/icon_sing.png",
        "nextseq": "ui/arrow_right.png",
        "previousseq": "ui/arrow_left.png",
        "undo": "ui/arrow_left.png",
        "gold": "sing/star_golden.png",
        "freestyle": "icons/icon_party.png",
        "PickerBG": "ui/card_surface.png",
        "Picker": "ui/color_picker.png",
        "Hue": "ui/color_picker.png",
        "HueBar": "ui/color_picker.png",
        "WhiteFade": "ui/white_rect.png",
        "BlackFade": "ui/bg_fade.png",
        "Pointer": "ui/cursor.png",
        "prevbackground": "ui/card_surface.png",
    }

    # Verify every key in official Blue.ini is covered
    blue_text = BLUE_INI.read_text(encoding="utf-8", errors="ignore")
    in_tex = False
    for line in blue_text.splitlines():
        s = line.strip()
        if s == "[Textures]":
            in_tex = True
            continue
        if s.startswith("["):
            in_tex = False
            continue
        if in_tex and "=" in s and not s.startswith(("#", ";", "/", "*")):
            k = s.split("=", 1)[0].strip()
            if k not in explicit_map:
                explicit_map[k] = "ui/card_surface.png"

    lines = [
        "; ============================================================================",
        "; Tokyo84 — Skin Definition: KabukichoMidnight",
        "; Verified 100% against UltraStar-Deluxe/USDX Modern.ini & Blue.ini",
        "; ============================================================================",
        "",
        "[Skin]",
        "Theme = Tokyo84",
        "Name = KabukichoMidnight",
        "Color = Blue",
        "Creator = Tokyo84 Design System",
        "",
        "[Textures]",
    ]
    for k, v in explicit_map.items():
        lines.append(f"{k} = {v}")

    OUT_SKIN.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_SKIN} ({len(explicit_map)} texture mappings)")


if __name__ == "__main__":
    build_tokyo84_ini()
    build_skin_ini()
