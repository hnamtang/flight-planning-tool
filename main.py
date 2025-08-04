from src.utils.args import parse_arguments
from src.utils.handle_arguments import (
    handle_api_key,
    run_cli,
    run_gui,
    validate_arguments,
)


def main():
    args = parse_arguments()

    if args.save_api_key:
        # Handle API key
        handle_api_key(args)
        return
    else:
        try:
            # Validate arguments
            validate_arguments(args)
        except ValueError as e:
            print(f"Argument error: {e}")
            return

    if args.no_gui:
        run_cli(args)
    else:
        run_gui(args)


if __name__ == "__main__":
    main()
