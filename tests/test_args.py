from pypixelcolor.lib.args import build_command_args

def test_build_command_args_positional():
    params = ["arg1", "arg2"]
    pos, kw = build_command_args(params)
    assert pos == ["arg1", "arg2"]
    assert kw == {}

def test_build_command_args_keyword():
    params = ["color=red", "font-size=16"]
    pos, kw = build_command_args(params)
    assert pos == []
    assert kw == {"color": "red", "font_size": "16"}

def test_build_command_args_mixed():
    params = ["hello", "speed=5", "world", "text-color=blue"]
    pos, kw = build_command_args(params)
    assert pos == ["hello", "world"]
    assert kw == {"speed": "5", "text_color": "blue"}
