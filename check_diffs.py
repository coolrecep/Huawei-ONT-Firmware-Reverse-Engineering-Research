def print_exact_diffs():
    # Let's print the absolute offsets of each string we found:
    offsets = {
        "flash_configA": 0xe702010,
        "flash_configB": 0xe7020bc,
        "slave_paramA":  0xe702168,
        "slave_paramB":  0xe702214,
        "allsystemA":    0xe7022c0,
        "allsystemB":    0xe70236c,
        "wifi_paramA":   0xe702442,
        "wifi_paramB":   0xe7024ee,
        "keyfile":       0xe70259a,
        "file_system":   0xe702646,
        "app_system":    0xe7026f2
    }
    
    prev_name = None
    prev_off = None
    for name, off in sorted(offsets.items(), key=lambda x: x[1]):
        if prev_off is not None:
            diff = off - prev_off
            print(f"{prev_name:<15} -> {name:<15} | Diff: {diff} bytes | Align 172: {diff % 172}")
        prev_name = name
        prev_off = off

if __name__ == "__main__":
    print_exact_diffs()
