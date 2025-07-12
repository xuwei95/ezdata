import type { Component } from 'vue';
// 注册组件
import PythonTask from './PythonTask.vue';
import ShellTask from './ShellTask.vue';
import SparkTask from './SparkTask.vue';
import FlinkTask from './FlinkTask.vue';
import EtlTask from './EtlTask/index.vue';
export type ComponentType = 'PythonTask' | 'ShellTask' | 'SparkTask' | 'FlinkTask' | 'EtlTask';

const componentMap = new Map<ComponentType, Component>();

componentMap.set('PythonTask', PythonTask);
componentMap.set('ShellTask', ShellTask);
componentMap.set('SparkTask', SparkTask);
componentMap.set('FlinkTask', FlinkTask);
componentMap.set('EtlTask', EtlTask);

export function add(compName: ComponentType, component: Component) {
  componentMap.set(compName, component);
}

export function del(compName: ComponentType) {
  componentMap.delete(compName);
}

export { componentMap };
