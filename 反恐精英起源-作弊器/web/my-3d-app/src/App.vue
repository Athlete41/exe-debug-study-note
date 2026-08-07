<template>
  <div style="width: 100vw; height: 100vh; background: #0a0a1a;">
    <ThreeCanvas
      :camera="camera"
      :elements="elements"
      :enable-orbit-controls="true"
      background-color="#0a0a1a"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ThreeCanvas from './components/ThreeCanvas.vue';

const camera = ref({
  position: [10, 5, 10],
  target: [0, 0, 0],
  fov: 60,
  near: 0.1,
  far: 1000,
});

const elements = ref([
  // 点（线框圆）
  { type: 'point', id: 'p1', position: [0, 0, 0], color: '#ff0000', size: 15 },
  { type: 'point', id: 'p2', position: [2, 0, 0], color: '#00ff00', size: 10 },

  // 线段
  { type: 'line', id: 'l1', points: [[-5, 0, 0], [5, 0, 0]], color: '#ffff00' },

  // 盒子
  { type: 'box', id: 'b1', position: [0, 2, 0], size: [1, 1, 1], color: '#00aaff' },

  // 文字
  { type: 'text', id: 't1', position: [0, 3, 0], text: 'Hello 3D', color: '#ffffff', fontSize: 20 },
]);

// 模拟动态更新
setInterval(() => {
  const newElements = [
    { type: 'point', id: 'p1', position: [Math.random() * 10 - 5, 0, 0], color: '#ff0000', size: 15 },
    { type: 'point', id: 'p3', position: [0, 0, Math.random() * 10 - 5], color: '#ff00ff', size: 12 },
    { type: 'line', id: 'l1', points: [[-5, 0, 0], [5, Math.random() * 4 - 2, 0]], color: '#ffff00' },
    { type: 'box', id: 'b1', position: [0, 2, 0], size: [1, Math.random() * 2 + 0.5, 1], color: '#00aaff' },
    { type: 'text', id: 't1', position: [0, 3, 0], text: `Time: ${Date.now()}`, color: '#ffffff', fontSize: 20 },
  ];
  elements.value = newElements;
}, 1000);
</script>