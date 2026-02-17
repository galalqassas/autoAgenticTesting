import json
import os
import random
import time

LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
DIFFICULTY = {"easy": 7, "medium": 5, "hard": 3}
SCORE_THRESHOLDS = [(10, 200), (20, 100)]
LANGUAGES = ["English", "French", "Spanish"]
STATS_FILE = "stats.json"
HIGH_SCORE_FILE = "high_score.txt"


def read_file(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f]


def get_random_word(words_list):
    return random.choice(words_list).upper()


def show_spaces(word):
    shown = set(random.sample(list(word), k=len(word) // 2))
    return [c if c in shown else "_" for c in word]


def is_file_exist(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' doesn't exist")
    return read_file(filename)


def get_high_score():
    if not os.path.exists(HIGH_SCORE_FILE):
        return 0
    with open(HIGH_SCORE_FILE, "r") as f:
        return int(f.read().strip() or 0)


def update_high_score(score, high_score):
    if score > high_score:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))
        return score
    return high_score


def is_valid(user_guess):
    return len(user_guess) == 1 and user_guess in LETTERS


def calc_score(elapsed_time, score):
    for max_time, points in SCORE_THRESHOLDS:
        if elapsed_time <= max_time:
            return score + points
    return score


def evaluation(elapsed_time, word_length):
    if elapsed_time >= 60:
        return "D"
    grades = {
        (True, "long"): "C+",
        (False, "long"): "C",
        (True, "medium"): "B+",
        (False, "medium"): "B",
        (True, "short"): "A+",
        (False, "short"): "A",
    }
    fast = elapsed_time < 30
    length = "long" if word_length > 7 else ("medium" if word_length == 7 else "short")
    return grades.get((fast, length), "C")


def set_language():
    language = input(f"Choose between {', '.join(LANGUAGES)}: ").title()
    while language not in LANGUAGES:
        language = input("Choose a valid language: ").title()
    return language


def would_the_user_like_to_play_again():
    choice = input("Play again? (1=yes, 2=no): ")
    while choice not in ("1", "2"):
        choice = input("Enter 1 or 2: ")
    return choice == "1"


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"games_played": 0, "wins": 0, "losses": 0, "total_time": 0.0}
    with open(STATS_FILE, "r") as f:
        return json.load(f)


def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def update_stats(won, game_time):
    stats = load_stats()
    stats["games_played"] += 1
    stats["wins" if won else "losses"] += 1
    stats["total_time"] += game_time
    save_stats(stats)
    return stats


def display_stats():
    stats = load_stats()
    games = stats["games_played"]
    if games == 0:
        return
    win_rate = (stats["wins"] / games) * 100
    avg_time = stats["total_time"] / games
    print(f"Stats: {games} games | {win_rate:.0f}% wins | {avg_time:.1f}s avg")


def play(word):
    score = 0
    game_start = time.time()
    previous_time = game_start
    blank_list = show_spaces(word)
    used_letters = set()

    level = input('Choose "easy", "medium" or "hard": ').lower()
    while level not in DIFFICULTY:
        level = input("Choose again: ").lower()
    tries = DIFFICULTY[level]

    print(f"Word: {''.join(blank_list)}")

    def get_guess():
        guess = input("Letter: ").upper()
        while not is_valid(guess):
            guess = input("Invalid, try again: ").upper()
        return guess

    won = False

    while tries > 0 and "_" in blank_list:
        guess = get_guess()
        elapsed_time = time.time() - previous_time
        previous_time = time.time()

        if guess in used_letters:
            print(f"Already guessed '{guess}'")
            continue

        used_letters.add(guess)

        # Check if guess reveals any NEW letters (hidden underscores)
        revealed = False
        for i, c in enumerate(word):
            if c == guess and blank_list[i] == "_":
                blank_list[i] = guess
                revealed = True

        if revealed:
            score = calc_score(elapsed_time, score)
            print(f"{''.join(blank_list)} | Score: {score}")
        elif guess in word:
            # Letter exists but already shown
            print(f"'{guess}' already visible!")
        else:
            tries -= 1
            print(f"Wrong! {tries} left")

    if "_" not in blank_list:
        won = True
        grade = evaluation(time.time() - game_start, len(word))
        print(f"You won! Grade: {grade}")
    else:
        print(f"Game over! Word: {word}")

    high_score = get_high_score()
    update_high_score(score, high_score)
    update_stats(won, time.time() - game_start)
    display_stats()
