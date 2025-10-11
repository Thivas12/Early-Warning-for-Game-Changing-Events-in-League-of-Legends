import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch.download import download_and_save_matches
from finalize.build_dataset import build_final_dataset

def main():
    """
    It runs the whole data pipeline by fetching matches, processing them, and building the final dataset.
    """
    parser = argparse.ArgumentParser(description="LoL data pipeline")
    parser.add_argument("--mode", choices=["full", "fetch", "finalize"], default="full")
    parser.add_argument("--input", help="Input CSV file path")
    parser.add_argument("--output", help="Output file or folder path")
    args = parser.parse_args()

    if args.mode == "fetch":
        if not args.input:
            print("Input CSV required for fetch mode")
            return
        output_file = args.output or "./data/interim/matches.csv"
        download_and_save_matches(args.input, output_file)

    elif args.mode == "finalize":
        if not args.input:
            print("Input CSV required for finalize mode")
            return
        output_dir = args.output or "./data/processed"
        build_final_dataset(args.input, output_dir)

    else:
        if not args.input:
            print("No input provided for full mode; exiting")
            return
        intermediate_file = "./data/interim/matches.csv"
        full_out_folder = "./data/processed"
        download_and_save_matches(args.input, intermediate_file)
        build_final_dataset(intermediate_file, full_out_folder)

if __name__ == "__main__":
    main()
