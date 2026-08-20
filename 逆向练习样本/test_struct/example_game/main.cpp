#define _CRT_SECURE_NO_WARNINGS  // 干掉 strcpy 警告
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

// ============================================
// 基础结构体
// ============================================

struct Vector3 {
    float x, y, z;
};

struct PlayerStats {
    int32_t health;
    int32_t armor;
    float speed;
    bool is_alive;
    uint8_t padding[3];
};

struct WeaponInfo {
    uint32_t weapon_id;
    int32_t damage;
    float fire_rate;
    char name[32];
    uint8_t level;
};

// ============================================
// 主结构体（带虚表）
// ============================================

struct GameWorld {
    virtual void Initialize() = 0;
    virtual void Update(float dt) = 0;
    virtual void Render() const = 0;
    virtual ~GameWorld() = default;

    uint32_t world_id;
    uint32_t frame_count;
    uint64_t tick_counter;

    void* renderer_ptr;
    void* physics_ptr;
    void* audio_ptr;
    void* input_ptr;
    void* network_ptr;

    Vector3 world_origin;
    Vector3 world_scale;
    PlayerStats global_stats;
    WeaponInfo default_weapon;

    Vector3 waypoints[8];
    float frame_times[16];
    uint32_t entity_ids[32];

    Vector3* dynamic_origin_ptr;
    PlayerStats* player_stats_ptr;
};

// ============================================
// GameWorld 实现类（定义+实现全在这里）
// ============================================

class GameWorldImpl : public GameWorld {
public:
    GameWorldImpl() {
        world_id = 0xDEADBEEF;
        frame_count = 0;
        tick_counter = 0;

        renderer_ptr = (void*)0x10000000;
        physics_ptr = (void*)0x20000000;
        audio_ptr = (void*)0x30000000;
        input_ptr = (void*)0x40000000;
        network_ptr = (void*)0x50000000;

        world_origin = { 0.0f, 0.0f, 0.0f };
        world_scale = { 1.0f, 1.0f, 1.0f };

        global_stats = { 100, 50, 1.5f, true, {0} };
        default_weapon = { 0x0001, 25, 0.5f, "Pistol", 1 };

        for (int i = 0; i < 8; i++) {
            waypoints[i] = { (float)(i * 10), (float)(i * 10), 0.0f };
        }
        for (int i = 0; i < 16; i++) frame_times[i] = 0.016f;
        for (int i = 0; i < 32; i++) entity_ids[i] = i + 100;

        dynamic_origin_ptr = new Vector3{ 5.0f, 5.0f, 5.0f };
        player_stats_ptr = new PlayerStats{ 100, 50, 1.5f, true, {0} };
    }

    ~GameWorldImpl() override {
        delete dynamic_origin_ptr;
        delete player_stats_ptr;
    }

    void Initialize() override {
        printf("[GameWorld] Init: 0x%X\n", world_id);
        frame_count = 0;
        global_stats.health = 100;
        global_stats.is_alive = true;
    }

    void Update(float dt) override {
        frame_count++;
        tick_counter += (uint64_t)(dt * 1000);
        global_stats.health -= (int32_t)(dt * 0.5f);
        if (global_stats.health < 0) {
            global_stats.health = 0;
            global_stats.is_alive = false;
        }
        waypoints[0].x += dt * 0.1f;
        if (dynamic_origin_ptr) {
            dynamic_origin_ptr->x += dt * global_stats.speed;
        }
        for (int i = 15; i > 0; i--) frame_times[i] = frame_times[i - 1];
        frame_times[0] = dt;
        printf("[Frame %u] Health: %d\n", frame_count, global_stats.health);
    }

    void Render() const override {
        printf("[Render] Health: %d, Weapon: %s\n",
            global_stats.health, default_weapon.name);
    }
};

// ============================================
// 全局变量 + 入口
// ============================================

extern "C" __declspec(dllexport) GameWorld* g_pWorld = nullptr;


int main() {
    printf("=== Game Starting ===\n");
    g_pWorld = new GameWorldImpl();
    g_pWorld->Initialize();

    for (int i = 0; i < 100; i++) {
        g_pWorld->Update(0.016f);
        if (i % 10 == 0) g_pWorld->Render();
    }

    delete g_pWorld;
    printf("=== Game Over ===\n");
    return 0;
}