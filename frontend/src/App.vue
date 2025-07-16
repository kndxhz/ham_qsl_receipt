<template>
  <div id="app">
    <el-container>
      <el-header>
        <el-menu
          :default-active="activeIndex"
          class="el-menu-demo"
          mode="horizontal"
          @select="handleSelect"
          :router="true"
        >
          <el-menu-item index="/">
            <el-icon><Document /></el-icon>
            <span>QSL回执</span>
          </el-menu-item>
          <el-menu-item index="/admin">
            <el-icon><Setting /></el-icon>
            <span>管理员</span>
          </el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { Document, Setting } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    Document,
    Setting
  },
  setup() {
    const route = useRoute()
    const activeIndex = ref(route.path)

    const handleSelect = (key) => {
      activeIndex.value = key
    }

    return {
      activeIndex,
      handleSelect
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}

.el-header {
  background-color: #545c64;
  color: #fff;
  padding: 0;
}

.el-menu-demo {
  background-color: #545c64;
}

.el-menu--horizontal > .el-menu-item {
  color: #fff;
}

.el-menu--horizontal > .el-menu-item:hover {
  background-color: #434a50;
}

.el-menu--horizontal > .el-menu-item.is-active {
  background-color: #409eff;
}

.el-main {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 60px);
}
</style>
