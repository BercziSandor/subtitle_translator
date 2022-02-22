import pytest

from src.subtitle_translator.main import *

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


@pytest.fixture
def google_translator():
    """Sample pytest fixture.
    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return GoogleTranslator(target='en')


def test_content(google_translator):
    """Sample pytest test function with the pytest fixture as an argument."""
    assert google_translator.translate(text='좋은') == "good"


def test_subtitle_translator():
    """
        Tests the project.
    """
    inp = ["hallo welt", "guten morgen"]
    outp = ['Helló Világ', "jó reggelt kívánok"]
    assert translate_array(texts=inp,
                           target_language='hu') == outp

    # translate_subtitle_file(input=sample_file)
