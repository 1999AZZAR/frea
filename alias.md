To make the code callable using the command `frea` from your bash terminal, you can create an alias for it in your bash profile configuration. Here's how you can do it:

1. Copy the `run_assist.sh` file from [here](code/run_assist.sh) and paste it to your liking. You can simply leave it there.

2. Open your bash profile file using a text editor. This file is typically named `.bashrc` or `.bash_profile` and is located in your home directory.

3. Add the following line to the file:

    ```bash
    alias frea="/path/to/run_assist.sh"
    ```

    Replace `/path/to/run_assist.sh` with the full path to the script you created earlier.

4. Save the file and close the text editor.

5. Now, to apply the changes, either restart your terminal or run the following command:

    ```bash
    source ~/.bashrc
    ```

    or

    ```bash
    source ~/.bash_profile
    ```

    This will reload your bash profile, and you should now be able to use the `frea` command to execute the script.

    When you type `frea` in your terminal, it will execute the script `run_assist.sh`, which performs the actions you described.
