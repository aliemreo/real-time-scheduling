# 🎨 Enhanced Terminal Visualization Features

## Overview
The enhanced `run_with_viz.py` script provides beautiful, colorful terminal visualizations for the Real-Time Scheduling (RTS) simulator output from `run_ali.cpp`.

## ✨ Key Features

### 1. **Colorful Output**
- **Color-coded task types:**
  - 🟢 Green: Periodic tasks (P)
  - 🟣 Magenta: Dynamic tasks (D)
  - 🔵 Cyan: Aperiodic tasks (A)
  - ⚪ White/Dim: IDLE time

- **Status indicators:**
  - ✓ Green: Successful completion (0 missed deadlines)
  - ✗ Red: Failed (missed deadlines detected)

### 2. **Enhanced Gantt Charts**
- Unicode box-drawing characters for professional appearance
- Clear task legends at the top of each chart
- Colored timeline bars (█) instead of plain blocks
- Dimmed idle time indicators (░)
- Time axis with tick marks and tens markers

### 3. **Visual Summary Statistics**
- Boxed summary sections showing:
  - Number of completed jobs
  - Number of missed deadlines
  - Details about which tasks missed deadlines
- Color-coded pass/fail indicators

### 4. **Algorithm Comparison Table**
- Side-by-side comparison of all scheduling algorithms
- Shows jobs completed, deadlines missed, and pass/fail status
- Makes it easy to compare algorithm performance at a glance

### 5. **Professional Headers**
- Stylized section headers with emojis (🚀, 📊, ✨)
- Clear visual separation between different schedulers
- Welcome banner and completion message

## 📋 Usage

```bash
python run_with_viz.py <input_file>
```

### Examples:
```bash
python run_with_viz.py example_periodic.txt
python run_with_viz.py example_aperiodic.txt
python run_with_viz.py example_overload.txt
```

## 🔧 Requirements

- **Python 3.6+**
- **colorama** library (for cross-platform colored terminal output)

### Installation:
```bash
pip install colorama
```

If `colorama` is not installed, the script will still work but without colors (fallback mode).

## 📊 Output Sections

### 1. Header
Shows input file name and compilation status

### 2. Individual Scheduler Visualizations
For each scheduler (RM, DM, EDF, LLF, Poller, Deferrable):
- Legend of tasks
- Gantt chart timeline
- Summary statistics box

### 3. Algorithm Comparison Table
Comparative view of all algorithms' performance

## 🎯 Visual Elements Explained

| Symbol | Meaning |
|--------|---------|
| █ | Task is executing (colored by task type) |
| ░ | Task is idle (not executing) |
| │ | Column separator |
| ─ | Row separator |
| ┌─┐ | Box drawing characters for statistics |

## 🌈 Color Scheme

The visualization uses ANSI color codes supported by most modern terminals:
- Works natively on Linux/macOS terminals
- Works on Windows with `colorama` library
- Automatically falls back to no-color mode if colors aren't supported

## 💡 Tips

1. **For best results**, use a terminal with:
   - UTF-8 encoding support
   - Color support (256 colors recommended)
   - Monospace font

2. **On Windows**, make sure to:
   - Use Windows Terminal, PowerShell, or modern cmd.exe
   - Have `colorama` installed

3. **Terminal width**: The visualization is optimized for 120+ character width terminals

## 🔄 Comparison: Before vs After

### Before:
```
--- Diagram for: Rate Monotonic Scheduling ---
T1(D) |··■■····■■······■■··■■······■■··■■······■■··■■
T2(D) |■···■···■···■···■···■···■···■···■···■···■···■
IDLE  |····■···········■····■·······■····■·······■····
```

### After:
```
════════════════════════════════════════════════════════════════════════════════
                          📊 Rate Monotonic Scheduling
════════════════════════════════════════════════════════════════════════════════

Legend:
  █ T1(D)  █ T2(D)  █ T3(P)

Task  │ Timeline (time units)
──────┼───────────────────────────────────────────────────
T1(D) │ ░██░░░██░░░░░██░░██░░░░░██░░░██░░░░░██░░░██░
T2(D) │ █░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░
IDLE  │ ░░░░░█░░░░█░░░░░█░░░███░░░█░█░░░███░░░█░█░░

┌────────────────────────────────────────────────────────┐
│ 📈 Summary Statistics                                   │
├────────────────────────────────────────────────────────┤
│ ✓ Completed Jobs:   25                                  │
│ ✗ Missed Deadlines: 0                                   │
└────────────────────────────────────────────────────────┘
```

## 🐛 Troubleshooting

**Issue:** Emojis not displaying correctly
- **Solution:** Update your terminal to support Unicode/UTF-8

**Issue:** Colors not showing
- **Solution:** Install colorama: `pip install colorama`

**Issue:** Garbled characters
- **Solution:** Ensure your terminal font supports Unicode box-drawing characters

## 📝 Technical Details

The visualization script:
1. Compiles `run_ali.cpp` (if needed)
2. Runs the RTS simulation
3. Parses the text output
4. Extracts scheduling events and statistics
5. Generates colorful Gantt charts
6. Creates comparison tables
7. Displays all results in an organized, visual format

All enhancements are backward-compatible and gracefully degrade if color/Unicode support is unavailable.
