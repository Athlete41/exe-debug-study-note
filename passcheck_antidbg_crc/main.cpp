/*
 * main.cpp
 * 密码验证程序 (GUI) + 反调试 + CRC 完整性自校验
 *
 * 首次设置 CRC：
 *   1. 编译运行（EXPECTED_CRC 保持 0 或错误值），MessageBox 会显示实际 CRC
 *   2. 将显示的 CRC 填入 EXPECTED_CRC
 *   3. 重新编译，即启用完整性校验
 *
 * 编译:
 *   g++ -O2 -s main.cpp -o passcheck_antidbg_crc.exe -mwindows
 *
 * -mwindows 去掉控制台窗口，仅显示 GUI 对话框。
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <intrin.h>     // __rdtsc

// ============================================================
// 首次编译时保持 0，运行后会弹 MessageBox 显示实际 CRC。
// ============================================================
#define EXPECTED_CRC           0

// NtQueryInformationProcess 参数
#define PROCESS_DEBUG_PORT     7

typedef LONG NTSTATUS;
typedef NTSTATUS (NTAPI *pfnNtQueryInformationProcess)(
    HANDLE, ULONG, PVOID, ULONG, PULONG
);

// 控件 ID
#define ID_EDIT_PASSWORD       1001

// ============================================================
// 标准表驱动 CRC32（多项式 0xEDB88320）
// ============================================================
static DWORD crc32_table[256];

static void crc32_init_table() {
    static bool initialized = false;
    if (initialized) return;
    initialized = true;
    for (DWORD i = 0; i < 256; i++) {
        DWORD crc = i;
        for (int j = 0; j < 8; j++) {
            if (crc & 1)
                crc = (crc >> 1) ^ 0xEDB88320;
            else
                crc >>= 1;
        }
        crc32_table[i] = crc;
    }
}

static DWORD crc32_compute(const BYTE* data, size_t len) {
    crc32_init_table();
    DWORD crc = 0xFFFFFFFF;
    for (size_t i = 0; i < len; i++) {
        crc = crc32_table[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
    }
    return crc ^ 0xFFFFFFFF;
}

// ============================================================
// CRC 完整性自检
// 解析当前进程的 PE 头，找到 .text 段在内存中的位置和大小，
// 对其计算 CRC32 并与 EXPECTED_CRC 比对。
//
// volatile + static const 保证 EXPECTED_CRC 存于 .rdata 段
// 而非作为立即数嵌在 .text 指令中，避免"改值就改 .text"的死循环。
// ============================================================
static const DWORD volatile g_expectedCrc = EXPECTED_CRC;

static bool check_integrity() {
    BYTE* base = (BYTE*)GetModuleHandleW(NULL);
    if (!base) return false;

    IMAGE_DOS_HEADER*  dos = (IMAGE_DOS_HEADER*)base;
    IMAGE_NT_HEADERS*  nt  = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
    IMAGE_SECTION_HEADER* sec = IMAGE_FIRST_SECTION(nt);

    BYTE* text_start = NULL;
    DWORD text_size  = 0;

    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (*(DWORD*)sec[i].Name == *(DWORD*)".text") {
            text_start = base + sec[i].VirtualAddress;
            text_size  = sec[i].SizeOfRawData;
            break;
        }
    }

    if (!text_start || text_size == 0)
        return false;

    DWORD computed = crc32_compute(text_start, text_size);

    // 首次运行：EXPECTED_CRC 未设 → MessageBox 输出实际 CRC 并放行
    if (g_expectedCrc == 0) {
        char buf[128];
        wsprintfA(buf, "Set EXPECTED_CRC to 0x%08X\n"
                       "Update the #define and recompile.",
                  computed);
        MessageBoxA(NULL, buf, "CRC Setup (first run)", MB_OK | MB_ICONINFORMATION);
        return true;
    }

    return (computed == g_expectedCrc);
}

// ============================================================
// 反调试检测
// ============================================================
static bool detect_debugger() {
    // ---- 检测 1: IsDebuggerPresent ----
    if (IsDebuggerPresent())
        return true;

    // ---- 检测 2: PEB → NtGlobalFlag ----
    // 调试器加载进程时 PEB.NtGlobalFlag 会被设为非零
#ifdef _WIN64
    BYTE* peb = (BYTE*)__readgsqword(0x60);
    DWORD ntGlobalFlag = *(DWORD*)(peb + 0xBC);
#else
    BYTE* peb = (BYTE*)__readfsdword(0x30);
    DWORD ntGlobalFlag = *(DWORD*)(peb + 0x68);
#endif
    if (ntGlobalFlag != 0)
        return true;

    // ---- 检测 3: NtQueryInformationProcess → ProcessDebugPort ----
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (hNtdll) {
        pfnNtQueryInformationProcess fn =
            (pfnNtQueryInformationProcess)GetProcAddress(
                hNtdll, "NtQueryInformationProcess");
        if (fn) {
            DWORD debugPort = 0;
            NTSTATUS status = fn(GetCurrentProcess(),
                                  PROCESS_DEBUG_PORT,
                                  &debugPort, sizeof(debugPort), NULL);
            if (status == 0 && debugPort != 0)
                return true;
        }
    }

    // ---- 检测 4: rdtsc 时间差（检测单步跟踪） ----
    // 正常 ~2000 周期，被单步跟踪可达数百万
    unsigned __int64 t1 = __rdtsc();
    volatile int dummy = 0;
    for (int i = 0; i < 200; i++)
        dummy += i;
    unsigned __int64 t2 = __rdtsc();

    if (t2 - t1 > 50000ULL)
        return true;

    return false;
}

// ============================================================
// 窗口过程
// ============================================================
LRESULT CALLBACK WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_CREATE: {
        HINSTANCE hInst = ((LPCREATESTRUCT)lParam)->hInstance;

        CreateWindowExW(0, L"STATIC", L"Enter password:",
            WS_CHILD | WS_VISIBLE,
            12, 12, 226, 15, hWnd, NULL, hInst, NULL);

        CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
            WS_CHILD | WS_VISIBLE | ES_PASSWORD | ES_AUTOHSCROLL,
            12, 30, 226, 22, hWnd, (HMENU)ID_EDIT_PASSWORD, hInst, NULL);

        CreateWindowExW(0, L"BUTTON", L"OK",
            WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON,
            12, 65, 100, 26, hWnd, (HMENU)IDOK, hInst, NULL);

        CreateWindowExW(0, L"BUTTON", L"Cancel",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            138, 65, 100, 26, hWnd, (HMENU)IDCANCEL, hInst, NULL);
        break;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK) {
            wchar_t buf[64] = {};
            GetDlgItemTextW(hWnd, ID_EDIT_PASSWORD, buf, 64);

            if (wcscmp(buf, L"secret123") == 0) {
                MessageBoxW(hWnd, L"Access Granted!", L"Result",
                            MB_OK | MB_ICONINFORMATION);
            } else {
                MessageBoxW(hWnd, L"Access Denied!", L"Result",
                            MB_OK | MB_ICONERROR);
            }
            DestroyWindow(hWnd);
        } else if (LOWORD(wParam) == IDCANCEL) {
            DestroyWindow(hWnd);
        }
        break;

    case WM_CLOSE:
        DestroyWindow(hWnd);
        break;

    case WM_DESTROY:
        PostQuitMessage(0);
        break;

    default:
        return DefWindowProcW(hWnd, msg, wParam, lParam);
    }
    return 0;
}

// ============================================================
// 入口点
// ============================================================
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {
    // 第 1 步：CRC 完整性自检
    if (!check_integrity()) {
        MessageBoxA(NULL, "Integrity check failed!", "Error", MB_OK | MB_ICONERROR);
        return -1;
    }

    // 第 2 步：反调试检测
    if (detect_debugger()) {
        MessageBoxA(NULL, "Debugger detected!", "Error", MB_OK | MB_ICONERROR);
        return -1;
    }

    // 第 3 步：注册窗口类
    const wchar_t CLASS_NAME[] = L"PassCheckClass";

    WNDCLASSEXW wc = {};
    wc.cbSize        = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc   = WndProc;
    wc.hInstance     = hInstance;
    wc.hCursor       = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.lpszClassName = CLASS_NAME;

    if (!RegisterClassExW(&wc))
        return -1;

    // 计算窗口尺寸（固定大小对话框风格）
    RECT rc = {0, 0, 250, 110};
    AdjustWindowRect(&rc, WS_CAPTION | WS_SYSMENU, FALSE);
    int win_w = rc.right - rc.left;
    int win_h = rc.bottom - rc.top;

    HWND hWnd = CreateWindowExW(0, CLASS_NAME, L"Password Check",
        WS_CAPTION | WS_SYSMENU,
        (GetSystemMetrics(SM_CXSCREEN) - win_w) / 2,
        (GetSystemMetrics(SM_CYSCREEN) - win_h) / 2,
        win_w, win_h,
        NULL, NULL, hInstance, NULL);

    if (!hWnd) return -1;

    ShowWindow(hWnd, nCmdShow);
    SetFocus(GetDlgItem(hWnd, ID_EDIT_PASSWORD));

    // 消息循环（IsDialogMessage 实现 Tab / Enter / Esc 导航）
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        if (!IsDialogMessageW(hWnd, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }

    return (int)msg.wParam;
}
