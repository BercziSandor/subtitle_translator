import io
import textwrap
from pathlib import Path

from src.subtitle_translator.main import get_subtitles_from_str, get_subtitles_from_file

sample_file = Path(__file__).parent.parent.parent.absolute() / Path('input/1.srt')
sample_str = io.StringIO(textwrap.dedent('''\
    1
    00:00:00,123 --> 00:00:03,456
    Hi there

    2
    00:01:04,843 --> 00:01:05,428
    This is an example of a
    subtitle file in SRT format
'''))


def test_subtitle_translator():
    """
        Tests the project.
    """

    subtitles = get_subtitles_from_str(sample_str)
    subtitles = get_subtitles_from_file(sample_file)

    pass
