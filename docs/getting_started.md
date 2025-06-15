# Getting Started

Run the `compare.ipynb` to perform the OpenMC simulations and compare them with precalculated FISPACT results and CoNDERC experimental data.

This can be run in several ways.

- With Jupyter Lab
    ```
    jupyter lab compare.ipynb
    ```

- With Jupyter
    ```
    jupyter notebook compare.ipynb
    ```

- With VS Code, assuming you have the Jupyter extension installed
    ```
    code compare.ipynb 
    ```

- Convert it to a python file and run with Python
    ```
    jupyter nbconvert compare.ipynb --to python
    python compare.py
    ```

- Build the book with Jupyter books.
    ```
    jupyter-book build .
    ```