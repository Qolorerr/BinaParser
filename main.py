from src.store_keeper import download_data

if __name__ == "__main__":
    test = "https://ru.bina.az/baki/kiraye/menziller?page=2&price_from=50&price_to=2000&room_ids%5B%5D=1&room_ids%5B%5D=2"
    download_data(test)
