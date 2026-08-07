<template>
  <div ref="containerRef" class="three-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick, shallowRef } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ============ 类型定义 ============
export interface CameraProps {
  position: [number, number, number];
  target?: [number, number, number];
  fov?: number;
  near?: number;
  far?: number;
}

// 所有元素都必须有 id，用于对象池匹配
export interface PointElement {
  type: 'point';
  id: string | number;
  position: [number, number, number];
  color?: string | number;
  size?: number; // 像素大小，默认 10
}

export interface LineElement {
  type: 'line';
  id: string | number;
  points: [number, number, number][]; // 长度必须为偶数
  color?: string | number;
}

export interface TextElement {
  type: 'text';
  id: string | number;
  position: [number, number, number];
  text: string;
  color?: string | number;
  fontSize?: number;
}

export interface BoxElement {
  type: 'box';
  id: string | number;
  position: [number, number, number];
  size: [number, number, number];
  color?: string | number;
}

export type Element = PointElement | LineElement | TextElement | BoxElement;

// ============ Props ============
const props = defineProps<{
  camera: CameraProps;
  elements: Element[];
  enableOrbitControls?: boolean;
  backgroundColor?: string | number;
}>();

// ============ 响应式引用 ============
const containerRef = ref<HTMLDivElement | null>(null);

// ============ Three.js 核心对象 ============
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls | null = null;
let animationId: number | null = null;

// 所有可渲染对象都挂在这个组下
const objectGroup = new THREE.Group();

// ============ 工具函数 ============
function toColor(color: string | number | undefined): THREE.Color {
  if (color === undefined) return new THREE.Color(0xffffff);
  return new THREE.Color(color);
}

function toThreePos(pos: [number, number, number]): THREE.Vector3 {
  return new THREE.Vector3(pos[0], pos[1], pos[2]);
}

// ============ 圆形纹理（线框圆，用于 Point） ============
let circleTexture: THREE.CanvasTexture | null = null;

function getCircleTexture(): THREE.CanvasTexture {
  if (circleTexture) return circleTexture;

  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d')!;

  const center = 32;
  const radius = 28;
  const lineWidth = 2;

  ctx.clearRect(0, 0, 64, 64);
  ctx.beginPath();
  ctx.arc(center, center, radius, 0, Math.PI * 2);
  ctx.strokeStyle = 'white';
  ctx.lineWidth = lineWidth;
  ctx.stroke();

  circleTexture = new THREE.CanvasTexture(canvas);
  circleTexture.needsUpdate = true;
  return circleTexture;
}

// ============ 对象池管理器 ============

/**
 * 点管理器
 * 使用 Sprite + 圆形纹理实现线框圆点
 */
class PointManager {
  private pool: Map<string | number, THREE.Sprite> = new Map();
  private group: THREE.Group;

  constructor(group: THREE.Group) {
    this.group = group;
  }

  sync(dataList: PointElement[]) {
    const activeIds = new Set(dataList.map(d => d.id));

    // 1. 更新或创建
    for (const data of dataList) {
      let sprite = this.pool.get(data.id);
      if (!sprite) {
        // 创建新 Sprite
        const texture = getCircleTexture();
        const material = new THREE.SpriteMaterial({
          map: texture,
          color: toColor(data.color),
          transparent: true,
          depthTest: false,
        });
        sprite = new THREE.Sprite(material);
        this.pool.set(data.id, sprite);
        this.group.add(sprite);
      }

      // 更新属性
      sprite.position.set(data.position[0], data.position[1], data.position[2]);
      const size = data.size ?? 10;
      // Sprite 的 scale 是三维的，我们只调整 x 和 y，z 保持 1
      sprite.scale.set(size, size, 1);
      sprite.material.color.set(toColor(data.color));
      sprite.visible = true;
    }

    // 2. 隐藏多余的对象
    for (const [id, sprite] of this.pool) {
      if (!activeIds.has(id)) {
        sprite.visible = false;
      }
    }
  }

  dispose() {
    for (const sprite of this.pool.values()) {
      sprite.material.dispose();
      // 纹理是全局共享的，不在这里 dispose
    }
    this.pool.clear();
  }
}

/**
 * 线管理器
 * 使用 LineSegments 渲染线段（每两个点构成一条线段）
 */
class LineManager {
  private pool: Map<string | number, THREE.LineSegments> = new Map();
  private group: THREE.Group;

  constructor(group: THREE.Group) {
    this.group = group;
  }

  sync(dataList: LineElement[]) {
    const activeIds = new Set(dataList.map(d => d.id));

    for (const data of dataList) {
      let line = this.pool.get(data.id);
      const pts = data.points;
      if (pts.length < 2) continue;

      if (!line) {
        // 创建新的 LineSegments
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(pts.length * 3);
        for (let i = 0; i < pts.length; i++) {
          positions[i * 3] = pts[i][0];
          positions[i * 3 + 1] = pts[i][1];
          positions[i * 3 + 2] = pts[i][2];
        }
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const material = new THREE.LineBasicMaterial({
          color: toColor(data.color),
        });
        line = new THREE.LineSegments(geometry, material);
        this.pool.set(data.id, line);
        this.group.add(line);
      } else {
        // 更新已有线段的顶点位置
        const geometry = line.geometry;
        const positionAttr = geometry.attributes.position;
        const array = positionAttr.array as Float32Array;
        const newLen = pts.length * 3;
        if (array.length !== newLen) {
          // 顶点数量变化，需要重新创建 BufferAttribute
          const newPositions = new Float32Array(newLen);
          for (let i = 0; i < pts.length; i++) {
            newPositions[i * 3] = pts[i][0];
            newPositions[i * 3 + 1] = pts[i][1];
            newPositions[i * 3 + 2] = pts[i][2];
          }
          geometry.setAttribute('position', new THREE.BufferAttribute(newPositions, 3));
          geometry.computeBoundingSphere();
        } else {
          // 顶点数量不变，直接更新数据
          for (let i = 0; i < pts.length; i++) {
            array[i * 3] = pts[i][0];
            array[i * 3 + 1] = pts[i][1];
            array[i * 3 + 2] = pts[i][2];
          }
          positionAttr.needsUpdate = true;
          geometry.computeBoundingSphere();
        }
        line.material.color.set(toColor(data.color));
      }

      line.visible = true;
    }

    // 隐藏多余的
    for (const [id, line] of this.pool) {
      if (!activeIds.has(id)) {
        line.visible = false;
      }
    }
  }

  dispose() {
    for (const line of this.pool.values()) {
      line.geometry.dispose();
      line.material.dispose();
    }
    this.pool.clear();
  }
}

/**
 * 盒子管理器
 * 使用 BoxGeometry + EdgesGeometry + LineSegments 渲染线框盒子
 */
class BoxManager {
  private pool: Map<string | number, THREE.LineSegments> = new Map();
  private group: THREE.Group;

  constructor(group: THREE.Group) {
    this.group = group;
  }

  sync(dataList: BoxElement[]) {
    const activeIds = new Set(dataList.map(d => d.id));

    for (const data of dataList) {
      let box = this.pool.get(data.id);
      const [w, h, d] = data.size;
      const pos = data.position;

      if (!box) {
        // 创建新的盒子
        const geometry = new THREE.BoxGeometry(w, h, d);
        const edges = new THREE.EdgesGeometry(geometry);
        const material = new THREE.LineBasicMaterial({
          color: toColor(data.color),
        });
        box = new THREE.LineSegments(edges, material);
        box.position.set(pos[0], pos[1], pos[2]);
        this.pool.set(data.id, box);
        this.group.add(box);
      } else {
        // 检查尺寸是否变化
        const currentGeo = box.geometry;
        // 获取原始 BoxGeometry（从 EdgesGeometry 中取出）
        // 由于 EdgesGeometry 不直接暴露原始几何体，我们通过比较顶点数量来简单判断
        // 更可靠的方式：在创建时存储尺寸，或者每次尺寸变化时重建
        // 简单起见：如果尺寸变化，重建几何体
        const positions = currentGeo.attributes.position?.array;
        if (positions) {
          // 简单检查：顶点数量是否符合当前尺寸的盒子
          // 一个盒子有 12 条边，每条边 2 个顶点，共 24 个顶点
          // 这里不精确判断，直接重建如果尺寸变化
          // 更精确：存储上一次的尺寸到 Map 中，但为了代码简洁，我们采用"尺寸变化就重建"策略
          // 因为尺寸变化频率通常不高
        }
        // 重建几何体（处理尺寸变化）
        const newGeo = new THREE.BoxGeometry(w, h, d);
        const newEdges = new THREE.EdgesGeometry(newGeo);
        // 替换几何体
        box.geometry.dispose();
        box.geometry = newEdges;
        box.position.set(pos[0], pos[1], pos[2]);
        box.material.color.set(toColor(data.color));
      }

      box.visible = true;
    }

    // 隐藏多余的
    for (const [id, box] of this.pool) {
      if (!activeIds.has(id)) {
        box.visible = false;
      }
    }
  }

  dispose() {
    for (const box of this.pool.values()) {
      box.geometry.dispose();
      box.material.dispose();
    }
    this.pool.clear();
  }
}

/**
 * 文字管理器
 * 使用 Sprite + Canvas 纹理渲染文字
 */
class TextManager {
  private pool: Map<string | number, THREE.Sprite> = new Map();
  private group: THREE.Group;

  constructor(group: THREE.Group) {
    this.group = group;
  }

  sync(dataList: TextElement[]) {
    const activeIds = new Set(dataList.map(d => d.id));

    for (const data of dataList) {
      let sprite = this.pool.get(data.id);

      if (!sprite) {
        // 创建新的文字 Sprite
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 256;
        const ctx = canvas.getContext('2d')!;
        // 先绘制到 canvas 上
        this.drawTextOnCanvas(ctx, canvas.width, canvas.height, data.text, data.color, data.fontSize);
        const texture = new THREE.CanvasTexture(canvas);
        texture.needsUpdate = true;
        const material = new THREE.SpriteMaterial({
          map: texture,
          transparent: true,
          depthTest: false,
        });
        sprite = new THREE.Sprite(material);
        // 将 canvas 和 texture 存到 sprite.userData 以便更新时复用
        sprite.userData.canvas = canvas;
        sprite.userData.texture = texture;

        this.pool.set(data.id, sprite);
        this.group.add(sprite);
      } else {
        // 更新已有文字
        const canvas = sprite.userData.canvas as HTMLCanvasElement;
        const ctx = canvas.getContext('2d')!;
        this.drawTextOnCanvas(ctx, canvas.width, canvas.height, data.text, data.color, data.fontSize);
        const texture = sprite.userData.texture as THREE.CanvasTexture;
        texture.needsUpdate = true;
        sprite.material.map = texture;
        sprite.material.color.set(toColor(data.color));
      }

      // 设置位置和缩放
      sprite.position.set(data.position[0], data.position[1], data.position[2]);
      // 文字大小：世界单位，根据场景调整
      const fontSize = data.fontSize ?? 14;
      const scale = fontSize / 50; // 调整比例
      sprite.scale.set(scale * 2, scale, 1);
      sprite.visible = true;
    }

    // 隐藏多余的
    for (const [id, sprite] of this.pool) {
      if (!activeIds.has(id)) {
        sprite.visible = false;
      }
    }
  }

  private drawTextOnCanvas(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    text: string,
    color: string | number | undefined,
    fontSize: number = 14
  ) {
    ctx.clearRect(0, 0, width, height);
    ctx.font = `${fontSize}px Arial, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = typeof color === 'string' ? color : (color !== undefined ? `#${color.toString(16).padStart(6, '0')}` : '#ffffff');
    ctx.fillText(text, width / 2, height / 2);
  }

  dispose() {
    for (const sprite of this.pool.values()) {
      (sprite.userData.texture as THREE.Texture)?.dispose();
      sprite.material.dispose();
    }
    this.pool.clear();
  }
}

// ============ 实例化管理器 ============
let pointManager: PointManager;
let lineManager: LineManager;
let boxManager: BoxManager;
let textManager: TextManager;

// ============ 更新场景 ============
function updateScene() {
  if (!scene) return;

  // 按类型分组
  const points = props.elements.filter((el): el is PointElement => el.type === 'point');
  const lines = props.elements.filter((el): el is LineElement => el.type === 'line');
  const boxes = props.elements.filter((el): el is BoxElement => el.type === 'box');
  const texts = props.elements.filter((el): el is TextElement => el.type === 'text');

  pointManager.sync(points);
  lineManager.sync(lines);
  boxManager.sync(boxes);
  textManager.sync(texts);
}

// ============ 更新相机 ============
function updateCamera() {
  if (!camera) return;

  const { position, target = [0, 0, 0], fov = 75, near = 0.1, far = 1000 } = props.camera;

  camera.position.set(position[0], position[1], position[2]);
  camera.lookAt(target[0], target[1], target[2]);
  camera.fov = fov;
  camera.near = near;
  camera.far = far;
  camera.updateProjectionMatrix();

  if (controls) {
    controls.target.set(target[0], target[1], target[2]);
    controls.update();
  }
}

// ============ 渲染循环 ============
function animate() {
  animationId = requestAnimationFrame(animate);
  if (controls) controls.update();
  renderer.render(scene, camera);
}

// ============ 初始化场景 ============
function initScene() {
  if (!containerRef.value) return;

  const container = containerRef.value;
  const width = container.clientWidth;
  const height = container.clientHeight;

  // 场景
  scene = new THREE.Scene();
  if (props.backgroundColor) {
    scene.background = new THREE.Color(props.backgroundColor);
  } else {
    scene.background = new THREE.Color(0x1a1a2e);
  }

  // 相机
  const { position, target = [0, 0, 0], fov = 75, near = 0.1, far = 1000 } = props.camera;
  camera = new THREE.PerspectiveCamera(fov, width / height, near, far);
  camera.position.set(position[0], position[1], position[2]);
  camera.lookAt(target[0], target[1], target[2]);

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // 轨道控制器
  if (props.enableOrbitControls !== false) {
    controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(target[0], target[1], target[2]);
    controls.update();
  }

  // 将 objectGroup 添加到场景
  scene.add(objectGroup);

  // 初始化管理器
  pointManager = new PointManager(objectGroup);
  lineManager = new LineManager(objectGroup);
  boxManager = new BoxManager(objectGroup);
  textManager = new TextManager(objectGroup);

  // 初始渲染元素
  updateScene();

  // 启动渲染循环
  animate();
}

// ============ 尺寸自适应 ============
function resizeRenderer() {
  if (!containerRef.value || !renderer || !camera) return;
  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;
  if (width === 0 || height === 0) return;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

// ============ 清理资源 ============
function disposeAll() {
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }

  pointManager?.dispose();
  lineManager?.dispose();
  boxManager?.dispose();
  textManager?.dispose();

  if (renderer) {
    renderer.dispose();
  }
  if (controls) {
    controls.dispose();
  }

  // 清理场景
  if (scene) {
    while (scene.children.length > 0) {
      const child = scene.children[0];
      scene.remove(child);
    }
  }
}

// ============ 生命周期 ============
onMounted(() => {
  nextTick(() => {
    initScene();
    window.addEventListener('resize', resizeRenderer);
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeRenderer);
  disposeAll();
});

// ============ 监听 Props 变化 ============
watch(
  () => props.camera,
  () => updateCamera(),
  { deep: true }
);

watch(
  () => props.elements,
  () => updateScene(),
  { deep: true }
);
</script>

<style scoped>
.three-container {
  width: 100%;
  height: 100%;
  display: block;
  overflow: hidden;
}

.three-container canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>