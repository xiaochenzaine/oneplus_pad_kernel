#!/system/bin/sh
# Read-only checks on the customer's device; run from a root shell.
set -eu

manager_package="${1:-com.sukisu.ultra}"
ordinary_package="${2:-}"

if [ "$(id -u)" != 0 ]; then
    echo "Run this script from a root shell to read other apps' /proc status."
    exit 1
fi

report_app() {
    app_package="$1"
    app_pids="$(pidof "$app_package" 2>/dev/null || true)"
    printf '\nPackage: %s\n' "$app_package"
    if [ -z "$app_pids" ]; then
        echo "Not running. Open the app, then repeat this check."
        return
    fi
    for app_pid in $app_pids; do
        printf 'PID: %s\n' "$app_pid"
        if [ -r "/proc/$app_pid/status" ]; then
            awk '/^(Name|Uid|NoNewPrivs|Seccomp|Seccomp_filters):/ { print }' "/proc/$app_pid/status" || true
        else
            echo "Status is unavailable; the process may have exited."
        fi
    done
}

printf 'Kernel: %s\n' "$(uname -r)"
printf 'Android: %s\n' "$(getprop ro.build.version.release)"
if [ -r /proc/config.gz ]; then
    echo "Built-in kernel support:"
    zcat /proc/config.gz | awk '/^CONFIG_SECCOMP(=|_FILTER=)/ { print }'
fi
report_app "$manager_package"
if [ -n "$ordinary_package" ]; then
    report_app "$ordinary_package"
fi
printf '\nSeccomp=2 means filter mode for the reported process.\n'
echo "A su/root shell may legitimately report Seccomp=0; do not use it as an app check."
echo "This script does not change filters, app permissions or device configuration."
