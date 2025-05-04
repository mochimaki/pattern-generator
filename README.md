# ADALM2000 Pattern Generator

A digital pattern generator application using ADALM2000. It can generate digital signal patterns for up to 16 channels and output them through ADALM2000.

## Main Features

- Digital signal pattern generation for up to 16 channels
- Graphical pattern editing interface
- Pattern save and load functionality
- CSV format export/import
- Real-time pattern playback
- Repeat playback functionality
- Individual channel control

## Requirements

- Python 3.8 or higher
- ADALM2000
- Required Python packages:
  - flet
  - pandas
  - libm2k

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Connect ADALM2000 to your computer and power it on.

## Usage

### Starting the Application

```bash
python pattern_generator.py
```

### Basic Operations

1. **Channel Selection**
   - Select the channel to edit from the dropdown menu at the top.

2. **Pattern Editing**
   - Set the state (High/Low) and duration, then click "Add" to add a pattern.
   - Select existing patterns to edit, delete, or copy them.
   - Use "Insert" buttons to add new patterns above or below the selected row.

3. **Pattern Save and Load**
   - Save current patterns via "File" → "Save" in the menu bar.
   - Load saved patterns via "File" → "Open".

4. **Pattern Playback**
   - Click the "Play" button to output patterns.
   - Configure sample rate and repeat count.

5. **Channel Control**
   - Enable/disable channels individually.
   - Set output values directly for each channel.

### Advanced Features

- **CSV Export/Import**
  - Export/import pattern data in CSV format.

- **Graph Display**
  - View pattern waveforms in a graph.

- **Repeat Playback**
  - Play patterns a specified number of times.
  - Infinite loop playback is also possible.

## Notes

- The application will not start if ADALM2000 is not properly connected.
- Always set an appropriate sample rate when editing patterns.
- Performance may degrade when handling large amounts of pattern data.

## Troubleshooting

1. **ADALM2000 Not Recognized**
   - Check ADALM2000 connection.
   - Verify the device's IP address is correctly configured.

2. **Pattern Not Outputting Correctly**
   - Check if the sample rate is properly set.
   - Verify that channels are enabled.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details. 