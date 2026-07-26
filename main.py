import dotenv

from utils.sync_data import sync_data

dotenv.load_dotenv()


def main():
    sync_data()


if __name__ == "__main__":
    main()
