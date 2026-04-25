#!/usr/bin/env python3
"""
mmWave Presence Diagnostics Visualizer
Companion tool for the Inovelli VZM32-SN mmWave blueprints.

Usage:
    pip install -r requirements.txt
    python app.py
    Open http://localhost:8050

Enter your HA URL, a long-lived access token (Profile → Security), and the
entity IDs for the occupancy and area sensors configured in the blueprint.
"""

import json
from datetime import datetime, timedelta, timezone

import dash
import plotly.graph_objects as go
import requests
from dash import Input, Output, State, ctx, dcc, html

# ── Constants ─────────────────────────────────────────────────────────────────

AREA_COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63"]
AREA_LABELS = ["Area 1", "Area 2", "Area 3", "Area 4"]

# Default zone bounds (Small room preset from blueprint)
DEFAULTS = [
    (-100, 100, 0, 200, -100, 100),
    (-100, 100, 0, 200, -100, 100),
    (-100, 100, 0, 200, -100, 100),
    (-100, 100, 0, 200, -100, 100),
]

BG = "#0f0f1a"
SIDEBAR_BG = "#1a1a2e"
CARD_BG = "#16213e"
BORDER = "#0f3460"
TEXT = "#e0e0e0"
ACCENT = "#e94560"

INPUT_STYLE = {
    "background": "#0a0a14",
    "border": f"1px solid {BORDER}",
    "color": TEXT,
    "borderRadius": "4px",
    "padding": "6px",
    "fontSize": "12px",
    "boxSizing": "border-box",
    "width": "100%",
}

# ── HA API ────────────────────────────────────────────────────────────────────


def ha_get_history(ha_url: str, token: str, entity_ids: list[str], hours: int = 24) -> list:
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"filter_entity_id": ",".join(entity_ids), "minimal_response": "true"}
    url = f"{ha_url.rstrip('/')}/api/history/period/{start.isoformat()}"
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def parse_history(raw: list) -> list[dict]:
    """Return a flat list of {entity_id, state, start, end, duration_s} dicts."""
    segments = []
    now = datetime.now(timezone.utc)
    for entity_history in raw:
        if not entity_history:
            continue
        entity_id = entity_history[0].get("entity_id", "")
        for i, obj in enumerate(entity_history):
            state = obj.get("state", "")
            changed = obj.get("last_changed") or obj.get("lu")
            if changed is None:
                continue
            start_ts = (
                datetime.fromtimestamp(changed, tz=timezone.utc)
                if isinstance(changed, (int, float))
                else datetime.fromisoformat(changed.replace("Z", "+00:00"))
            )
            if i + 1 < len(entity_history):
                nxt = entity_history[i + 1].get("last_changed") or entity_history[i + 1].get("lu")
                end_ts = (
                    datetime.fromtimestamp(nxt, tz=timezone.utc)
                    if isinstance(nxt, (int, float))
                    else datetime.fromisoformat(nxt.replace("Z", "+00:00"))
                )
            else:
                end_ts = now
            segments.append(
                {
                    "entity_id": entity_id,
                    "state": state,
                    "start": start_ts,
                    "end": end_ts,
                    "duration_s": (end_ts - start_ts).total_seconds(),
                }
            )
    return segments


# ── 3D helpers ────────────────────────────────────────────────────────────────


def _box_edges(x1, x2, y1, y2, z1, z2):
    """12 wireframe edges as None-separated Scatter3d coordinate lists."""
    pairs = [
        # bottom
        ((x1,y1,z1),(x2,y1,z1)), ((x2,y1,z1),(x2,y2,z1)),
        ((x2,y2,z1),(x1,y2,z1)), ((x1,y2,z1),(x1,y1,z1)),
        # top
        ((x1,y1,z2),(x2,y1,z2)), ((x2,y1,z2),(x2,y2,z2)),
        ((x2,y2,z2),(x1,y2,z2)), ((x1,y2,z2),(x1,y1,z2)),
        # verticals
        ((x1,y1,z1),(x1,y1,z2)), ((x2,y1,z1),(x2,y1,z2)),
        ((x2,y2,z1),(x2,y2,z2)), ((x1,y2,z1),(x1,y2,z2)),
    ]
    xs, ys, zs = [], [], []
    for a, b in pairs:
        xs += [a[0], b[0], None]
        ys += [a[1], b[1], None]
        zs += [a[2], b[2], None]
    return xs, ys, zs


def _box_mesh(x1, x2, y1, y2, z1, z2):
    """8-vertex, 12-triangle Mesh3d for a box."""
    vx = [x1, x2, x2, x1, x1, x2, x2, x1]
    vy = [y1, y1, y2, y2, y1, y1, y2, y2]
    vz = [z1, z1, z1, z1, z2, z2, z2, z2]
    # 6 faces × 2 triangles each
    fi = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
    fj = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
    fk = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]
    return vx, vy, vz, fi, fj, fk


# ── Figure builders ───────────────────────────────────────────────────────────


def build_3d_figure(zones: list[dict], segments: list[dict], fp_start=None, fp_end=None):
    traces = []

    # Switch at origin
    traces.append(
        go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode="markers+text",
            marker=dict(size=10, color="white", symbol="square",
                        line=dict(color="yellow", width=2)),
            text=["Switch"], textposition="top center",
            name="Switch",
            hovertext="VZM32-SN<br>Switch face at origin",
            hoverinfo="text",
        )
    )

    for idx, zone in enumerate(zones):
        if not zone.get("configured"):
            continue
        x1, x2 = zone["x_min"], zone["x_max"]
        y1, y2 = zone["y_min"], zone["y_max"]
        z1, z2 = zone["z_min"], zone["z_max"]
        color = AREA_COLORS[idx]
        label = AREA_LABELS[idx]
        entity = zone.get("entity_id", "")

        on_segs = [s for s in segments if s["entity_id"] == entity and s["state"] == "on"]
        fp_segs = (
            [s for s in on_segs if s["start"] <= fp_end and s["end"] >= fp_start]
            if fp_start and fp_end
            else []
        )
        has_events = bool(on_segs)
        is_fp_zone = bool(fp_segs)

        # Wireframe
        ex, ey, ez = _box_edges(x1, x2, y1, y2, z1, z2)
        traces.append(
            go.Scatter3d(
                x=ex, y=ey, z=ez,
                mode="lines",
                line=dict(color=color, width=3),
                name=label,
                opacity=0.9 if has_events else 0.35,
                hoverinfo="skip",
            )
        )

        # Filled mesh
        vx, vy, vz, fi, fj, fk = _box_mesh(x1, x2, y1, y2, z1, z2)
        traces.append(
            go.Mesh3d(
                x=vx, y=vy, z=vz,
                i=fi, j=fj, k=fk,
                color=color,
                opacity=0.13 if has_events else 0.04,
                name=f"{label} fill",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Event marker at zone centre
        cx, cy, cz = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
        if has_events:
            count = len(on_segs)
            hover = (
                f"<b>{label}</b><br>"
                f"Detections (24h): {count}<br>"
                f"Zone: X[{x1},{x2}] Y[{y1},{y2}] Z[{z1},{z2}] cm"
            )
            traces.append(
                go.Scatter3d(
                    x=[cx], y=[cy], z=[cz],
                    mode="markers",
                    marker=dict(size=6 + min(count * 2, 14), color=color,
                                opacity=0.85, symbol="circle"),
                    name=f"{label} events",
                    hovertext=hover, hoverinfo="text",
                    showlegend=False,
                )
            )

        # False-positive halo
        if is_fp_zone:
            hover_fp = (
                f"<b>{label} — FALSE POSITIVE</b><br>"
                f"{len(fp_segs)} event(s) in selected window<br>"
                f"Zone: X[{x1},{x2}] Y[{y1},{y2}] Z[{z1},{z2}] cm"
            )
            traces.append(
                go.Scatter3d(
                    x=[cx], y=[cy], z=[cz],
                    mode="markers",
                    marker=dict(size=24, color="red", opacity=0.55,
                                symbol="circle-open",
                                line=dict(width=4, color="red")),
                    name=f"{label} false positive",
                    hovertext=hover_fp, hoverinfo="text",
                    showlegend=False,
                )
            )

    fig = go.Figure(data=traces)
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X — left/right (cm)", gridcolor="#2a2a4a", color="#888",
                       backgroundcolor=BG),
            yaxis=dict(title="Y — depth into room (cm)", gridcolor="#2a2a4a", color="#888",
                       backgroundcolor=BG),
            zaxis=dict(title="Z — up/down (cm)", gridcolor="#2a2a4a", color="#888",
                       backgroundcolor=BG),
            bgcolor=BG,
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.0)),
            aspectmode="data",
        ),
        paper_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Inter, Segoe UI, Arial, sans-serif"),
        legend=dict(bgcolor="#1a1a2e", bordercolor=BORDER, borderwidth=1,
                    font=dict(size=11)),
        margin=dict(l=0, r=0, t=10, b=0),
        height=500,
    )
    return fig


def build_timeline_figure(
    segments: list[dict],
    entity_labels: dict[str, str],
    fp_start=None,
    fp_end=None,
):
    now = datetime.now(timezone.utc)
    start_24h = now - timedelta(hours=24)

    ordered = sorted(entity_labels.items(), key=lambda kv: (kv[1] != "Overall", kv[1]))
    y_map = {eid: i for i, (eid, _) in enumerate(ordered)}

    fig = go.Figure()

    for eid, label in ordered:
        idx = list(entity_labels.keys()).index(eid)
        color = AREA_COLORS[max(0, idx - 1)] if label != "Overall" else "#78909C"
        y = y_map[eid]

        for seg in (s for s in segments if s["entity_id"] == eid and s["state"] == "on"):
            is_fp = (
                fp_start and fp_end
                and seg["start"] <= fp_end
                and seg["end"] >= fp_start
            )
            fig.add_shape(
                type="rect",
                x0=seg["start"], x1=seg["end"],
                y0=y - 0.38, y1=y + 0.38,
                fillcolor="red" if is_fp else color,
                opacity=0.85 if is_fp else 0.6,
                line=dict(width=0),
            )
            # Invisible hover dot
            mid = seg["start"] + (seg["end"] - seg["start"]) / 2
            dur = int(seg["duration_s"])
            m, s = divmod(dur, 60)
            dur_str = f"{m}m {s}s" if m else f"{s}s"
            fp_tag = "  ⚠ FP WINDOW" if is_fp else ""
            fig.add_trace(
                go.Scatter(
                    x=[mid], y=[y],
                    mode="markers",
                    marker=dict(size=1, opacity=0),
                    hovertext=(
                        f"<b>{label}</b>{fp_tag}<br>"
                        f"Start: {seg['start'].strftime('%H:%M:%S')} UTC<br>"
                        f"End:   {seg['end'].strftime('%H:%M:%S')} UTC<br>"
                        f"Duration: {dur_str}"
                    ),
                    hoverinfo="text",
                    showlegend=False,
                )
            )

    if fp_start and fp_end:
        fig.add_vrect(
            x0=fp_start, x1=fp_end,
            fillcolor="red", opacity=0.12,
            annotation_text="FP Window",
            annotation_position="top left",
            annotation=dict(font=dict(color="red", size=10)),
        )

    y_labels = [label for _, label in ordered]
    fig.update_layout(
        xaxis=dict(
            range=[start_24h, now],
            title="Last 24 hours (UTC)",
            color="#888", gridcolor="#2a2a4a",
            tickformat="%H:%M",
        ),
        yaxis=dict(
            tickvals=list(range(len(y_labels))),
            ticktext=y_labels,
            color="#888", gridcolor="#2a2a4a",
        ),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, Segoe UI, Arial, sans-serif"),
        height=220,
        margin=dict(l=70, r=20, t=10, b=50),
        showlegend=False,
        dragmode="select",
    )
    return fig


# ── Recommendations ───────────────────────────────────────────────────────────


def generate_recommendations(
    zones: list[dict],
    segments: list[dict],
    fp_start,
    fp_end,
    device_name: str = "<device-friendly-name>",
) -> str:
    if not fp_start or not fp_end:
        return (
            "*Select a false positive window in the **Timeline** tab (drag to zoom), "
            "then click **Analyze** to generate recommendations.*"
        )

    triggered = []
    for idx, zone in enumerate(zones):
        if not zone.get("configured"):
            continue
        entity = zone.get("entity_id", "")
        fp_segs = [
            s for s in segments
            if s["entity_id"] == entity
            and s["state"] == "on"
            and s["start"] <= fp_end
            and s["end"] >= fp_start
        ]
        if fp_segs:
            triggered.append((idx, zone, fp_segs))

    if not triggered:
        return (
            "**No detection events found in the selected window.**  \n"
            "Try widening the false positive time range."
        )

    start_str = fp_start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = fp_end.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"## False Positive Analysis",
        f"**Window (UTC):** {start_str} → {end_str}\n",
        "### Triggered Zones\n",
    ]

    for idx, zone, segs in triggered:
        label = AREA_LABELS[idx]
        avg_dur = sum(s["duration_s"] for s in segs) / len(segs)
        lines += [
            f"**{label}** — {len(segs)} event(s), avg duration {avg_dur:.0f}s  ",
            f"Zone bounds: X[{zone['x_min']}, {zone['x_max']}]  "
            f"Y[{zone['y_min']}, {zone['y_max']}]  "
            f"Z[{zone['z_min']}, {zone['z_max']}] cm\n",
        ]

    lines += ["---", "### Option 1 — Add Interference Area(s) in Zigbee2MQTT\n",
              "In Z2M → device → Configure, add Interference Areas:\n"]

    for idx, zone, _ in triggered:
        label = AREA_LABELS[idx]
        cfg = {
            "x_min": zone["x_min"], "x_max": zone["x_max"],
            "y_min": zone["y_min"], "y_max": zone["y_max"],
            "z_min": zone["z_min"], "z_max": zone["z_max"],
        }
        lines += [
            f"```json",
            f"// Interference Area — {label} false positives",
            json.dumps(cfg, indent=2),
            "```\n",
        ]

    lines += [
        "---",
        "### Option 2 — Auto-generate Interference Area via MQTT\n",
        "While a false positive is **actively occurring**, publish:\n",
        "```",
        f"Topic:   zigbee2mqtt/{device_name}/set",
        'Payload: {"controlSequence": {"control": 1}}',
        "```",
        "This triggers Control ID 0x01, capturing the current target as Interference Area 0.\n",
        "---",
        "### Option 3 — Shrink Detection Zone(s)\n",
        "Reduce **Y_max** of triggering zone(s) to exclude the false-positive area:\n",
    ]
    for idx, zone, _ in triggered:
        new_y = max(0, zone["y_max"] - 30)
        lines.append(
            f"- **{AREA_LABELS[idx]}**: Y_max {zone['y_max']} cm → ~{new_y} cm"
        )
    lines.append(
        "\n*Apply one option at a time, re-run the automation for a day, "
        "and repeat until false positives are eliminated.*"
    )

    return "\n".join(lines)


# ── Layout helpers ────────────────────────────────────────────────────────────


def _zone_card(n: int) -> html.Div:
    label = AREA_LABELS[n]
    color = AREA_COLORS[n]
    x1, x2, y1, y2, z1, z2 = DEFAULTS[n]

    def coord_row(axis, lo_id, hi_id, lo_val, hi_val):
        mini = dict(INPUT_STYLE, width="46%", fontFamily="monospace", fontSize="11px")
        return html.Div(
            [
                html.Label(axis, style={"fontSize": "10px", "color": "#666",
                                        "width": "14px", "flexShrink": 0}),
                dcc.Input(id=lo_id, type="number", value=lo_val, style=mini),
                html.Span("→", style={"color": "#555", "margin": "0 4px"}),
                dcc.Input(id=hi_id, type="number", value=hi_val, style=mini),
            ],
            style={"display": "flex", "alignItems": "center", "marginBottom": "4px"},
        )

    return html.Div(
        [
            html.Div(label, style={"color": color, "fontWeight": "700",
                                   "fontSize": "11px", "marginBottom": "5px",
                                   "letterSpacing": "0.05em"}),
            coord_row("X", f"z{n+1}-x1", f"z{n+1}-x2", x1, x2),
            coord_row("Y", f"z{n+1}-y1", f"z{n+1}-y2", y1, y2),
            coord_row("Z", f"z{n+1}-z1", f"z{n+1}-z2", z1, z2),
        ],
        style={
            "background": f"{color}0f",
            "border": f"1px solid {color}33",
            "borderRadius": "6px",
            "padding": "8px",
            "marginBottom": "8px",
        },
    )


def _label(text: str) -> html.Div:
    return html.Div(text, style={"fontSize": "10px", "color": "#666",
                                 "textTransform": "uppercase",
                                 "letterSpacing": "0.08em",
                                 "marginBottom": "4px", "marginTop": "10px"})


def _section(title: str) -> html.Div:
    return html.Div(
        title,
        style={"fontSize": "10px", "fontWeight": "700", "color": "#555",
               "textTransform": "uppercase", "letterSpacing": "0.1em",
               "marginBottom": "8px", "marginTop": "14px",
               "borderBottom": f"1px solid {BORDER}", "paddingBottom": "4px"},
    )


TAB_STYLE = {"background": CARD_BG, "color": "#666", "border": "none",
             "padding": "8px 14px", "fontSize": "12px"}
TAB_SEL_STYLE = {**TAB_STYLE, "color": TEXT, "borderTop": f"2px solid {ACCENT}"}

# ── App layout ────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, title="mmWave Diagnostics — VZM32-SN")
app.layout = html.Div(
    [
        dcc.Store(id="history-store", storage_type="session"),

        # ── Header ──────────────────────────────────────────────────────────
        html.Div(
            [
                html.Span("mmWave Presence Diagnostics",
                          style={"fontWeight": "700", "fontSize": "15px",
                                 "letterSpacing": "0.08em"}),
                html.Span("  VZM32-SN · Zigbee2MQTT",
                          style={"color": "#555", "fontSize": "11px"}),
            ],
            style={"background": SIDEBAR_BG, "padding": "12px 20px",
                   "borderBottom": f"1px solid {BORDER}",
                   "display": "flex", "alignItems": "center"},
        ),

        # ── Body ─────────────────────────────────────────────────────────────
        html.Div(
            [
                # ── Sidebar ──────────────────────────────────────────────────
                html.Div(
                    [
                        _section("HA Connection"),
                        _label("URL"),
                        dcc.Input(id="ha-url", type="text",
                                  placeholder="http://homeassistant.local:8123",
                                  style=dict(INPUT_STYLE, marginBottom="6px")),
                        _label("Long-lived Token"),
                        dcc.Input(id="ha-token", type="password",
                                  placeholder="eyJ…",
                                  style=dict(INPUT_STYLE, marginBottom="6px")),
                        _label("Z2M Device Name (for MQTT commands)"),
                        dcc.Input(id="device-name", type="text",
                                  placeholder="Living Room Switch",
                                  style=dict(INPUT_STYLE, marginBottom="6px")),

                        _section("Entity IDs"),
                        _label("Occupancy (required)"),
                        dcc.Input(id="e-occ", type="text",
                                  placeholder="binary_sensor.mmwave_occupancy",
                                  style=dict(INPUT_STYLE, fontFamily="monospace",
                                             fontSize="11px", marginBottom="4px")),
                        *[
                            html.Div(
                                [
                                    _label(f"Area {i+1} (optional)"),
                                    dcc.Input(
                                        id=f"e-a{i+1}", type="text",
                                        placeholder=f"binary_sensor.mmwave_area{i+1}",
                                        style=dict(INPUT_STYLE, fontFamily="monospace",
                                                   fontSize="11px",
                                                   borderColor=f"{AREA_COLORS[i]}55",
                                                   marginBottom="4px"),
                                    ),
                                ]
                            )
                            for i in range(4)
                        ],

                        _section("Zone Configuration (cm)"),
                        html.Div("Enter the X/Y/Z bounds configured in Z2M for each area.",
                                 style={"fontSize": "10px", "color": "#555",
                                        "marginBottom": "8px"}),
                        *[_zone_card(n) for n in range(4)],

                        html.Button(
                            "Fetch & Visualize", id="fetch-btn", n_clicks=0,
                            style={"width": "100%", "background": ACCENT,
                                   "color": "white", "border": "none",
                                   "borderRadius": "6px", "padding": "10px",
                                   "cursor": "pointer", "fontSize": "13px",
                                   "fontWeight": "700", "marginTop": "6px"},
                        ),
                        html.Div(id="fetch-status",
                                 style={"marginTop": "7px", "fontSize": "11px",
                                        "color": "#888", "textAlign": "center",
                                        "minHeight": "16px"}),
                    ],
                    style={
                        "width": "280px", "minWidth": "280px",
                        "background": SIDEBAR_BG,
                        "padding": "14px 14px 20px",
                        "overflowY": "auto",
                        "height": "calc(100vh - 44px)",
                        "borderRight": f"1px solid {BORDER}",
                        "boxSizing": "border-box",
                    },
                ),

                # ── Main ─────────────────────────────────────────────────────
                html.Div(
                    [
                        # False-positive window row
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div("False Positive Window (UTC)",
                                                 style={"fontSize": "10px",
                                                        "color": "#666",
                                                        "textTransform": "uppercase",
                                                        "letterSpacing": "0.08em",
                                                        "marginBottom": "5px"}),
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="fp-start", type="text",
                                                    placeholder="YYYY-MM-DD HH:MM:SS",
                                                    style={**INPUT_STYLE, "width": "190px",
                                                           "fontFamily": "monospace",
                                                           "marginRight": "8px"},
                                                ),
                                                html.Span("→", style={"color": "#555",
                                                                       "marginRight": "8px"}),
                                                dcc.Input(
                                                    id="fp-end", type="text",
                                                    placeholder="YYYY-MM-DD HH:MM:SS",
                                                    style={**INPUT_STYLE, "width": "190px",
                                                           "fontFamily": "monospace",
                                                           "marginRight": "12px"},
                                                ),
                                                html.Button(
                                                    "Analyze", id="analyze-btn", n_clicks=0,
                                                    style={"background": "#1a5c38",
                                                           "color": "white", "border": "none",
                                                           "borderRadius": "5px",
                                                           "padding": "7px 16px",
                                                           "cursor": "pointer",
                                                           "fontSize": "12px",
                                                           "fontWeight": "700",
                                                           "marginRight": "6px"},
                                                ),
                                                html.Button(
                                                    "Clear", id="clear-btn", n_clicks=0,
                                                    style={"background": "#2a2a3a",
                                                           "color": "#888", "border": "none",
                                                           "borderRadius": "5px",
                                                           "padding": "7px 12px",
                                                           "cursor": "pointer",
                                                           "fontSize": "12px"},
                                                ),
                                            ],
                                            style={"display": "flex", "alignItems": "center"},
                                        ),
                                        html.Div(
                                            "Tip: drag-zoom on the Timeline to auto-fill these fields, then click Analyze.",
                                            style={"fontSize": "10px", "color": "#555",
                                                   "marginTop": "5px", "fontStyle": "italic"},
                                        ),
                                    ]
                                ),
                            ],
                            style={"background": CARD_BG, "border": f"1px solid {BORDER}",
                                   "borderRadius": "8px", "padding": "12px 14px",
                                   "marginBottom": "10px"},
                        ),

                        # Tabs
                        dcc.Tabs(
                            [
                                dcc.Tab(
                                    label="3D View",
                                    children=[
                                        dcc.Graph(id="graph-3d",
                                                  figure=build_3d_figure([], []),
                                                  config={"displayModeBar": True,
                                                          "modeBarButtonsToRemove": ["toImage"]},
                                                  style={"height": "500px"}),
                                    ],
                                    style=TAB_STYLE, selected_style=TAB_SEL_STYLE,
                                ),
                                dcc.Tab(
                                    label="Timeline",
                                    children=[
                                        dcc.Graph(
                                            id="graph-timeline",
                                            figure=build_timeline_figure([], {}, None, None),
                                            config={"displayModeBar": False},
                                            style={"height": "220px"},
                                        ),
                                        html.Div(
                                            "Drag on the chart to zoom into a time range — "
                                            "the False Positive Window fields above will auto-fill.",
                                            style={"fontSize": "10px", "color": "#555",
                                                   "padding": "6px 12px",
                                                   "fontStyle": "italic"},
                                        ),
                                    ],
                                    style=TAB_STYLE, selected_style=TAB_SEL_STYLE,
                                ),
                                dcc.Tab(
                                    label="Recommendations",
                                    children=[
                                        dcc.Markdown(
                                            id="recs-text",
                                            children=(
                                                "*Fetch sensor history, then select a false "
                                                "positive window in the Timeline to generate "
                                                "recommendations.*"
                                            ),
                                            style={"padding": "16px", "color": TEXT,
                                                   "fontSize": "13px", "lineHeight": "1.7",
                                                   "maxHeight": "560px", "overflowY": "auto"},
                                        ),
                                    ],
                                    style=TAB_STYLE, selected_style=TAB_SEL_STYLE,
                                ),
                            ],
                            style={"background": CARD_BG, "border": f"1px solid {BORDER}",
                                   "borderRadius": "8px"},
                        ),
                    ],
                    style={"flex": "1", "padding": "10px 12px",
                           "overflowY": "auto",
                           "height": "calc(100vh - 44px)",
                           "boxSizing": "border-box"},
                ),
            ],
            style={"display": "flex", "height": "calc(100vh - 44px)"},
        ),
    ],
    style={"background": BG, "color": TEXT,
           "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
           "margin": 0, "padding": 0},
)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("history-store", "data"),
    Output("fetch-status", "children"),
    Input("fetch-btn", "n_clicks"),
    State("ha-url", "value"),
    State("ha-token", "value"),
    State("e-occ", "value"),
    State("e-a1", "value"),
    State("e-a2", "value"),
    State("e-a3", "value"),
    State("e-a4", "value"),
    prevent_initial_call=True,
)
def fetch_history(_, ha_url, token, occ, a1, a2, a3, a4):
    if not ha_url or not token or not occ:
        return None, "⚠ Enter HA URL, token, and occupancy entity."
    entities = [e for e in [occ, a1, a2, a3, a4] if e]
    try:
        raw = ha_get_history(ha_url, token, entities)
        segs = parse_history(raw)
        # Serialise datetimes for dcc.Store
        for s in segs:
            s["start"] = s["start"].isoformat()
            s["end"] = s["end"].isoformat()
        on_count = sum(1 for s in segs if s["state"] == "on")
        return {"segments": segs, "entities": entities}, f"✓ {on_count} presence events loaded."
    except requests.HTTPError as exc:
        return None, f"HTTP {exc.response.status_code}: {exc.response.text[:60]}"
    except Exception as exc:  # noqa: BLE001
        return None, f"Error: {str(exc)[:80]}"


@app.callback(
    Output("fp-start", "value"),
    Output("fp-end", "value"),
    Input("graph-timeline", "relayoutData"),
    prevent_initial_call=True,
)
def sync_fp_from_zoom(relayout):
    """Auto-populate FP window when user drag-zooms the timeline."""
    if relayout and "xaxis.range[0]" in relayout:
        # Plotly emits ISO strings like "2026-02-28 14:32:00"
        raw_start = relayout["xaxis.range[0]"]
        raw_end = relayout["xaxis.range[1]"]
        # Trim to seconds
        return raw_start[:19], raw_end[:19]
    return dash.no_update, dash.no_update


def _deserialise(store_data):
    segs = (store_data or {}).get("segments", [])
    for s in segs:
        s["start"] = datetime.fromisoformat(s["start"])
        s["end"] = datetime.fromisoformat(s["end"])
    return segs, (store_data or {}).get("entities", [])


def _parse_fp(start_str, end_str):
    try:
        fp_s = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc) if start_str else None
        fp_e = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc) if end_str else None
        return fp_s, fp_e
    except ValueError:
        return None, None


def _build_zones(entities, zone_vals):
    area_entities = entities[1:] if len(entities) > 1 else []
    zones = []
    for i, (x1, x2, y1, y2, z1, z2) in enumerate(zone_vals):
        zones.append({
            "entity_id": area_entities[i] if i < len(area_entities) else "",
            "configured": all(v is not None for v in (x1, x2, y1, y2, z1, z2)),
            "x_min": x1 or 0, "x_max": x2 or 0,
            "y_min": y1 or 0, "y_max": y2 or 0,
            "z_min": z1 or 0, "z_max": z2 or 0,
        })
    return zones


@app.callback(
    Output("graph-3d", "figure"),
    Output("graph-timeline", "figure"),
    Output("recs-text", "children"),
    Input("history-store", "data"),
    Input("analyze-btn", "n_clicks"),
    Input("clear-btn", "n_clicks"),
    State("e-occ", "value"), State("e-a1", "value"), State("e-a2", "value"),
    State("e-a3", "value"), State("e-a4", "value"),
    State("device-name", "value"),
    State("z1-x1", "value"), State("z1-x2", "value"),
    State("z1-y1", "value"), State("z1-y2", "value"),
    State("z1-z1", "value"), State("z1-z2", "value"),
    State("z2-x1", "value"), State("z2-x2", "value"),
    State("z2-y1", "value"), State("z2-y2", "value"),
    State("z2-z1", "value"), State("z2-z2", "value"),
    State("z3-x1", "value"), State("z3-x2", "value"),
    State("z3-y1", "value"), State("z3-y2", "value"),
    State("z3-z1", "value"), State("z3-z2", "value"),
    State("z4-x1", "value"), State("z4-x2", "value"),
    State("z4-y1", "value"), State("z4-y2", "value"),
    State("z4-z1", "value"), State("z4-z2", "value"),
    State("fp-start", "value"), State("fp-end", "value"),
    prevent_initial_call=True,
)
def update_views(
    store_data, _analyze, _clear,
    occ, a1, a2, a3, a4, device_name,
    z1x1, z1x2, z1y1, z1y2, z1z1, z1z2,
    z2x1, z2x2, z2y1, z2y2, z2z1, z2z2,
    z3x1, z3x2, z3y1, z3y2, z3z1, z3z2,
    z4x1, z4x2, z4y1, z4y2, z4z1, z4z2,
    fp_start_str, fp_end_str,
):
    triggered = ctx.triggered_id
    segs, entities = _deserialise(store_data)

    # Resolve entities list from current inputs (store may lag behind)
    all_entities = [e for e in [occ, a1, a2, a3, a4] if e]
    if all_entities:
        entities = all_entities

    zone_vals = [
        (z1x1, z1x2, z1y1, z1y2, z1z1, z1z2),
        (z2x1, z2x2, z2y1, z2y2, z2z1, z2z2),
        (z3x1, z3x2, z3y1, z3y2, z3z1, z3z2),
        (z4x1, z4x2, z4y1, z4y2, z4z1, z4z2),
    ]
    zones = _build_zones(entities, zone_vals)

    fp_start, fp_end = None, None
    if triggered == "analyze-btn":
        fp_start, fp_end = _parse_fp(fp_start_str, fp_end_str)

    entity_labels: dict[str, str] = {}
    if occ:
        entity_labels[occ] = "Overall"
    for i, e in enumerate([a1, a2, a3, a4]):
        if e:
            entity_labels[e] = AREA_LABELS[i]

    fig_3d = build_3d_figure(zones, segs, fp_start, fp_end)
    fig_tl = build_timeline_figure(segs, entity_labels, fp_start, fp_end)
    recs = generate_recommendations(
        zones, segs, fp_start, fp_end, device_name or "<device-friendly-name>"
    )
    return fig_3d, fig_tl, recs


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
