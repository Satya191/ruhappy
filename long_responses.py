import random

R_ADVICE = 'Here are some strategies to uplift your day or reduce stress: https://bit.ly/3AMXXVp'
R_HAPPY = 'Here is a playlist of songs that will definitely make you happier: https://bit.ly/3lMSqK8'


def unknown():
    response = ["Could you please re-phrase that? ",
                "...",
                "Sounds about right.",
                "What does that mean?"][
        random.randrange(4)]
    return response