Module replicate.files
======================

Functions
---------

    
`upload_file(file: io.IOBase, output_file_prefix: Optional[str] = None) ‑> str`
:   Upload a file to the server.
    
    Args:
        file: A file handle to upload.
        output_file_prefix: A string to prepend to the output file name.
    Returns:
        str: A URL to the uploaded file.