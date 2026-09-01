# Entry point. Run with `python main.py` for an interactive chat loop.

from agent import handle_message


def main():
    while True:
        question = input("Ask Something or Quit: ")
        if question.lower() == "quit":
            break
        handle_message(question)


if __name__ == "__main__":
    main()
