from datetime import datetime, timedelta


def get_ending_time(
    current_time: datetime, clip_length: int, offset: int = 0
) -> datetime:
    """
    Calculate the ending time of a block based on the current time and
    block size.

    For example, if the current time is 14:23:45 and the block size is 300
    seconds (5 minutes), then the current block starts at 14:20:00 and ends
    at 14:25:00. This function will return 14:25:00 as the ending time of
    the block.

    Args:
        current_time (datetime): The current time.
        clip_length (int): The size of the block in seconds.
        offset (int): Offset in seconds to adjust the block end time.

    Returns:
        datetime: The ending time of the block.
    """
    current_full_hour = current_time.replace(minute=0, second=0, microsecond=0)
    current_block = (current_time - current_full_hour).total_seconds() // clip_length
    current_block_end = current_full_hour + timedelta(
        seconds=(current_block + 1) * clip_length + offset
    )
    return current_block_end
