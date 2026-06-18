// 内置组件任务模板(type=1)的前端表单组件注册表。
// 任务模板的 component 字段(或 code)映射到此处的 Vue 组件；任务表单据此动态渲染。
import PythonTask from './PythonTask.vue'
import ShellTask from './ShellTask.vue'
import DataIntegrationTask from './DataIntegrationTask.vue'

const componentMap = {
  PythonTask,
  ShellTask,
  DataIntegrationTask
}

export function getTaskComponent(name) {
  return name ? componentMap[name] : undefined
}

export { componentMap }
