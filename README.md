# PrestaShop to Shopify Exporter

This project exports products from PrestaShop to Shopify. It fetches product data from PrestaShop, processes it, and saves it in a format suitable for Shopify.

## Project Structure

- `dump/`: Directory where the exported Shopify products are saved.
- `dump_products.py`: Contains the logic to fetch and process products from PrestaShop.
- `main.py`: Entry point of the application.
- `ps_services.py`: Contains functions to interact with the PrestaShop API.
- `shopify_types.py`: Defines data structures for Shopify products.
- `todo.txt`: List of tasks to be completed.
- `.env`: Environment variables for PrestaShop API credentials.
- `.gitignore`: Specifies files and directories to be ignored by Git.

## Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/freakspace/prestashop_export_shopify
    cd prestashop_export_shopify
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a [.env](http://_vscodecontentref_/6) file with your PrestaShop API credentials:
    ```
    PS_API_KEY=your_prestashop_api_key
    PS_API_URL=your_prestashop_api_url
    ```

## Usage

To export products from PrestaShop to Shopify, run the following command:
```sh
python main.py
```

This will fetch products from PrestaShop, process them, and save the output in
```sh
dump/shopfiy_products.py
```

Use the json file to import products to Shopify