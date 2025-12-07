# RTS Simulator - Enhanced Visualizations

## Overview
Two visualization scripts are now available for the Real-Time Scheduling (RTS) simulator:

1. **run_with_viz.py** - Enhanced terminal/console visualization with colors
2. **run_graphical_viz.py** - Graphical PNG output matching the reference style

## 📊 Graphical Visualization (NEW!)

### Usage:
```bash
python run_graphical_viz.py <input_file>
```

### Example:
```bash
python run_graphical_viz.py example_periodic.txt
python run_graphical_viz.py example_aperiodic.txt
```

### Features:
✅ **Grid Background** - Professional grid layout with vertical and horizontal lines
✅ **Arrival Arrows** - Solid upward arrows (↑) showing when tasks arrive
✅ **Deadline Arrows** - Dashed downward arrows (↓) showing task deadlines
✅ **Color-Coded Tasks**:
- 🔴 Red: Task 1
- 🔵 Blue: Task 2
- 🟠 Orange: Task 3 (with /// pattern)
- 🟢 Green: Task 4 (with xxx pattern)
- ⚪ Light Gray: IDLE time

✅ **Timeline Bar** - Bottom section showing actual task execution
✅ **Time Axis** - Both top and bottom with numbered time units
✅ **Legend** - Shows all tasks with their colors and patterns
✅ **Summary Box** - Displays completed jobs and missed deadlines
✅ **High-Resolution PNG Output** - Saves at 200 DPI for presentations

### Output Files:
The script generates PNG files for each scheduling algorithm:
- `schedule_Rate_Monotonic_Scheduling.png`
- `schedule_Deadline_Monotonic_Scheduling.png`
- `schedule_Earliest_Deadline_First_Scheduling.png`
- `schedule_Least_Laxity_First_Scheduling.png`
- `schedule_Poller_Scheduling_Scheduling.png` (for aperiodic)
- `schedule_Deferrable_Scheduling_Scheduling.png` (for aperiodic)

## 🎨 Terminal Visualization

### Usage:
```bash
python run_with_viz.py <input_file>
```

### Features:
- Colorful terminal output with ANSI colors
- Text-based Gantt charts using Unicode characters
- Real-time progress indicators
- Comparison tables
- Summary statistics boxes

See [VISUALIZATION_FEATURES.md](VISUALIZATION_FEATURES.md) for detailed terminal visualization features.

## 📋 Requirements

### For Graphical Visualization:
- Python 3.6+
- matplotlib
- numpy

### For Terminal Visualization:
- Python 3.6+
- colorama

### Installation:
```bash
pip install matplotlib numpy colorama
```

## 🎯 Comparison: Terminal vs Graphical

| Feature | Terminal (run_with_viz.py) | Graphical (run_graphical_viz.py) |
|---------|---------------------------|-----------------------------------|
| Output Format | Text/Unicode in console | PNG image files |
| Colors | ANSI terminal colors | Full RGB colors |
| Arrows | Text symbols | Graphical arrows |
| Patterns | Limited | Full hatching patterns (///, xxx) |
| Grid | Text-based | Professional grid lines |
| Export | Copy from terminal | High-res PNG files |
| Presentation | Console viewing | Reports, papers, slides |
| Interactive | Live in terminal | Save and share files |

## 📊 Example Outputs

### Graphical Visualization:
![Example](schedule_Rate_Monotonic_Scheduling.png)

Features visible in graphical output:
- Grid background with vertical time markers
- Red, blue, and orange arrows showing task arrivals and deadlines
- Color-coded timeline bar at bottom
- Clear task patterns (solid, diagonal lines, cross-hatch)
- Professional appearance suitable for reports and presentations

### Terminal Visualization:
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
T3(P) │ ░░░█░█░░░█░░░░░█░█░░░█░░░░░█░█░░░█░░░░░█░█░
IDLE  │ ░░░░░█░░░░█░░░░░█░░░███░░░█░█░░░███░░░█░█░░
```

## 🚀 Quick Start Guide

### Step 1: Run the C++ Simulator
The visualization scripts automatically compile and run your C++ simulator.

### Step 2: Choose Your Visualization

**For quick console viewing:**
```bash
python run_with_viz.py example_periodic.txt
```

**For professional graphical output:**
```bash
python run_graphical_viz.py example_periodic.txt
```

### Step 3: View Results
- **Terminal**: Results displayed immediately in console
- **Graphical**: Open generated PNG files

## 🔧 Customization

### Graphical Visualization Customization:
Edit [run_graphical_viz.py](run_graphical_viz.py):

- **Colors**: Modify `task_colors` dictionary (line 126-139)
- **Patterns**: Modify `task_patterns` dictionary (line 142-147)
- **Figure Size**: Change `figsize` parameter (line 150)
- **DPI**: Modify `dpi` parameter (line 278)
- **Grid Spacing**: Adjust grid drawing loops (lines 161-166)

### Terminal Visualization Customization:
Edit [run_with_viz.py](run_with_viz.py):

- **Colors**: Modify color assignments in `get_task_color()` function
- **Characters**: Change timeline characters (█, ░, etc.)
- **Box Styles**: Modify `print_box()` and `print_header()` functions

## 📝 Tips for Best Results

### Graphical Visualization:
1. **File Format**: PNG format is best for presentations and documents
2. **Resolution**: Default 200 DPI works well for most uses
3. **Viewing**: Open PNG files with any image viewer
4. **Editing**: Can be edited in image editors if needed
5. **Sharing**: Easy to include in reports, slides, emails

### Terminal Visualization:
1. **Terminal Width**: Use at least 120 characters wide terminal
2. **Font**: Monospace font recommended
3. **Colors**: Works best in modern terminals (Windows Terminal, iTerm2, etc.)
4. **Screenshot**: Take screenshots for documentation if needed

## 🐛 Troubleshooting

**Issue:** "matplotlib not found"
**Solution:** `pip install matplotlib numpy`

**Issue:** "colorama not found" (terminal viz)
**Solution:** `pip install colorama`

**Issue:** "Executable not found"
**Solution:** Compile your C++ code first: `g++ -o run_ali.exe run_ali.cpp` (or use make)

**Issue:** PNG files not appearing
**Solution:** Check current directory, files are saved where script is run

**Issue:** Arrows not aligned properly
**Solution:** Task periods are auto-detected; may need to adjust periods in script for custom tasks

## 📚 Use Cases

### Terminal Visualization Best For:
- Quick debugging and testing
- Live monitoring during development
- Console-based environments
- Quick comparisons
- CI/CD pipeline output

### Graphical Visualization Best For:
- Academic papers and reports
- Presentations and slides
- Documentation
- Sharing results via email
- High-quality publications
- Detailed analysis

## 🎓 Example Workflow

1. **Development Phase**: Use terminal visualization for quick feedback
   ```bash
   python run_with_viz.py test_case.txt
   ```

2. **Documentation Phase**: Generate graphical outputs
   ```bash
   python run_graphical_viz.py test_case.txt
   ```

3. **Presentation Phase**: Use generated PNG files in your slides/documents

## 📊 Advanced Features (Graphical)

The graphical visualization matches professional scheduling diagrams with:
- IEEE conference paper quality
- Publication-ready resolution
- Standard scheduling notation (arrows for arrivals/deadlines)
- Clear visual separation of task types
- Professional color scheme
- Grid-based layout following academic standards

Perfect for:
- 📄 Research papers
- 📊 Technical reports
- 🎓 Academic presentations
- 📋 Documentation
- 📧 Email attachments

---

**Both visualization tools work together to provide comprehensive analysis of your RTS simulator output!**
