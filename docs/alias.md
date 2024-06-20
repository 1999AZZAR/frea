To make the code callable using the command `frea` from your bash terminal, you can create an alias for it in your bash profile configuration. Here's how you can do it:

1. open the `frea` file from `src/` folder.

2. edit that file, edit the part to the main.py path it self.

3. Open your bash profile file using a text editor. This file is typically named `.bashrc` or `.bash_profile` and is located in your home directory.

4. Add the following line to the file:

    ```bash
    alias frea="/path/to/frea"
    ```

    Replace `/path/to/frea` with the full path to the script you created earlier eg. `downloads/src/frea`.

5. Save the file and close the text editor.

6. Now, to apply the changes, either restart your terminal or run the following command:

    ```bash
    source ~/.bashrc
    ```

    or

    ```bash
    source ~/.bash_profile
    ```

    This will reload your bash profile, and you should now be able to use the `frea` command to execute the script.
    When you type `frea` in your terminal, it will execute the script `frea`, which performs the actions you described.
