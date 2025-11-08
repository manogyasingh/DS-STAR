import sys
from pathlib import Path
from textwrap import indent

from ds_star import DSSTAR
from llm_clients import GeminiClient as LLMClient

CONSOLE_WIDTH = 72


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        print("\nInput stream closed. Exiting.")
        sys.exit(0)


def print_rule(char: str = "-", title: str | None = None) -> None:
    if title:
        print(title.center(CONSOLE_WIDTH, char))
    else:
        print(char * CONSOLE_WIDTH)


def print_banner() -> None:
    print_rule("=")
    print("DS-STAR Interactive Console".center(CONSOLE_WIDTH))
    print_rule("=")


def print_section(title: str) -> None:
    print()
    print_rule("-")
    print(title.upper().center(CONSOLE_WIDTH))
    print_rule("-")


def prompt_query() -> str:
    print_section("Describe Your Query")
    print(
        "Fill in the details of the data science question or task you want DS-STAR "
        "to solve.\nEnter multiple lines if needed; submit an empty line to finish."
    )

    lines: list[str] = []
    while True:
        line = safe_input("query> ")
        if not line.strip():
            if lines:
                break
            print("Please provide at least one line describing your query.")
            continue
        lines.append(line)

    return "\n".join(lines).strip()


def prompt_data_files() -> list[str]:
    print_section("Attach Data Files")
    print(
        "Add the data files you want the solver to use. Provide one path per line. "
        "Press Enter on a blank line when you are done.\n"
        "Commands: 'list' to view the current selection, 'clear' to remove all files."
    )

    files: list[str] = []
    while True:
        entry = safe_input("files> ").strip()
        if not entry:
            break

        command = entry.lower()
        if command in {"list", "ls"}:
            if files:
                print("\nCurrent file selection:")
                for idx, path in enumerate(files, 1):
                    print(f"  {idx}. {path}")
                print()
            else:
                print("No files selected yet.")
            continue

        if command == "clear":
            files.clear()
            print("Cleared all selected files.")
            continue

        candidate = Path(entry).expanduser()
        if candidate.exists():
            resolved = str(candidate.resolve())
            files.append(resolved)
            print(f"  ✓ Added {resolved}")
        else:
            print(f"  ! File not found: {candidate}")
            choice = safe_input("    Add anyway? [y/N]: ").strip().lower()
            if choice in {"y", "yes"}:
                files.append(entry)
                print(f"  ✓ Added (unverified) {entry}")

    return files


def confirm_inputs(query: str, data_files: list[str]) -> bool:
    print_section("Review Inputs")
    print("Query:")
    print(indent(query, "  "))

    print("\nData files:")
    if data_files:
        for idx, path in enumerate(data_files, 1):
            print(f"  {idx}. {path}")
    else:
        print("  (none)")

    while True:
        response = safe_input(
            "\nProceed with these inputs? [Y/n/q]: "
        ).strip().lower()
        if response in {"", "y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        if response in {"q", "quit"}:
            print("Aborting. Goodbye!")
            sys.exit(0)
        print("Please respond with 'y', 'n', or 'q'.")


def collect_user_inputs() -> tuple[str, list[str]]:
    while True:
        query = prompt_query()
        data_files = prompt_data_files()
        if confirm_inputs(query, data_files):
            return query, data_files
        print("\nLet's try that again.\n")


def main() -> None:
    llm_client = LLMClient(max_tokens=1000000)
    ds_star = DSSTAR(
        llm_client=llm_client,
        max_refinement_rounds=10,
        max_debug_attempts=3,
    )

    print_banner()
    try:
        query, data_files = collect_user_inputs()
    except KeyboardInterrupt:
        print("\nSession interrupted. Goodbye!")
        sys.exit(0)

    print_section("Solving")
    print("Submitting your request to DS-STAR... please wait.\n")

    final_code, plan, results = ds_star.solve(query, data_files)

    print_section("Final Solution Code")
    print(final_code or "(no code returned)")

    print_section("Final Plan")
    if plan:
        for idx, step in enumerate(plan, 1):
            print(f"{idx}. {step}")
    else:
        print("(plan not available)")

    if results:
        print_section("Results")
        print(results)


if __name__ == "__main__":
    main()
