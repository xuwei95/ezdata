import type { Component } from 'vue';
// 注册组件
import TaskFailStrategy from './TaskFailStrategy.vue';
export type ComponentType = 'TaskFailStrategy';

const componentMap = new Map<ComponentType, Component>();

componentMap.set('TaskFailStrategy', TaskFailStrategy);

export function add(compName: ComponentType, component: Component) {
  componentMap.set(compName, component);
}

export function del(compName: ComponentType) {
  componentMap.delete(compName);
}
export const TemplateCodeOptions = [{ label: '任务失败告警', value: 'TaskFailStrategy' }];

export { componentMap };
