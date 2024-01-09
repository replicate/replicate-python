import tempfile

import pytest

import replicate


@pytest.mark.vcr("file-operations.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_file_operations(async_flag):
    # Create a sample file
    with tempfile.NamedTemporaryFile(
        mode="wb", delete=False, prefix="test_file", suffix=".txt"
    ) as temp_file:
        temp_file.write(b"Hello, Replicate!")

        # Test create
        if async_flag:
            created_file = await replicate.files.async_create(temp_file.name)
        else:
            created_file = replicate.files.create(temp_file.name)

    assert created_file.name.startswith("test_file")
    assert created_file.name.endswith(".txt")
    file_id = created_file.id

    # Test get
    if async_flag:
        retrieved_file = await replicate.files.async_get(file_id)
    else:
        retrieved_file = replicate.files.get(file_id)

    assert retrieved_file.id == file_id

    # Test list
    if async_flag:
        file_list = await replicate.files.async_list()
    else:
        file_list = replicate.files.list()

    assert file_list is not None
    assert len(file_list) > 0
    assert any(f.id == file_id for f in file_list)

    # Test delete
    if async_flag:
        await replicate.files.async_delete(file_id)
    else:
        replicate.files.delete(file_id)

    # Verify file is deleted
    if async_flag:
        file_list = await replicate.files.async_list()
    else:
        file_list = replicate.files.list()

    assert all(f.id != file_id for f in file_list)
