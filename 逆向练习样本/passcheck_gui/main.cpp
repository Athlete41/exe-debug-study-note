#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <intrin.h>
#include <stdio.h>

#define ID_EDIT_PASSWORD       1001

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
            // 关闭窗口
            // DestroyWindow(hWnd);
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


int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {
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

    // 消息循环（ IsDialogMessage 实现 Tab / Enter / Esc 导航）
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        if (!IsDialogMessageW(hWnd, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }

    return (int)msg.wParam;
}
