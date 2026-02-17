from functions import (
    display_stats,
    get_random_word,
    is_file_exist,
    play,
    set_language,
    would_the_user_like_to_play_again,
)


def main():
    display_stats()
    filename = set_language() + ".txt"
    words_list = is_file_exist(filename)

    while True:
        word = get_random_word(words_list)  # New word each game
        play(word)
        if not would_the_user_like_to_play_again():
            break

    print("Thanks for playing!")


if __name__ == "__main__":
    main()
