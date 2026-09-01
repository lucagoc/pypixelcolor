# Other Commands

## `set_fun_mode`

::: pypixelcolor.commands.set_fun_mode.set_fun_mode
    options:
      show_root_heading: false
      show_root_toc_entry: false

## `set_pixel`

::: pypixelcolor.commands.set_fun_mode.set_pixel
    options:
      show_root_heading: false
      show_root_toc_entry: false

## `set_rhythm_mode`

::: pypixelcolor.commands.set_rhythm_mode.set_rhythm_mode
    options:
      show_root_heading: false
      show_root_toc_entry: false

## `set_rhythm_mode_2`

::: pypixelcolor.commands.set_rhythm_mode.set_rhythm_mode_2
    options:
      show_root_heading: false
      show_root_toc_entry: false

## `set_timer`

Controls the timer (stopwatch) mode on the device.

::: pypixelcolor.commands.set_timer.set_timer
    options:
      show_root_heading: false
      show_root_toc_entry: false

**Examples:**

```python
# Start, pause or stop the timer
client.set_timer("start")
client.set_timer("pause")
client.set_timer("stop")
```

```bash
pypixelcolor -a <MAC_ADDRESS> -c set_timer start
```

## `set_scores`

Sets the scoreboard scores for player 1 and player 2 on supported devices.

::: pypixelcolor.commands.set_scores.set_scores
    options:
      show_root_heading: false
      show_root_toc_entry: false

**Examples:**

```python
# Set Player 1 to 24 and Player 2 to 18
client.set_scores(score_p1=24, score_p2=18)
```

```bash
pypixelcolor -a <MAC_ADDRESS> -c set_scores score_p1=24 score_p2=18
```

