import os


def get_free_space(pathname):
    st = os.statvfs(pathname)
    total = st.f_blocks * st.f_frsize
    used = st.f_frsize * (st.f_blocks - st.f_bfree)
    if total > 0:
        return 100 - (100 * (float(used) / total))
    return 100
