import { PropType } from 'vue';

export type Theme = 'vs' | 'hc-black' | 'vs-dark';
export type FoldingStrategy = 'auto' | 'indentation';
export type RenderLineHighlight = 'all' | 'line' | 'none' | 'gutter';
export interface Options {
  automaticLayout: boolean; // 自适应布局
  foldingStrategy: FoldingStrategy; // 折叠方式  auto | indentation
  renderLineHighlight: RenderLineHighlight; // 行亮
  selectOnLineNumbers: boolean; // 显示行号
  placeholder: string;
  minimap: {
    // 关闭小地图
    enabled: boolean;
  };
  // readOnly: Boolean // 只读
  fontSize: number; // 字体大小
  scrollBeyondLastLine: boolean; // 取消代码后面一大段空白
  overviewRulerBorder: boolean; // 不要滚动条的边框
}

export const editorProps = {
  value: {
    type: String as PropType<string>,
    default: null,
  },
  hightChange: {
    type: Boolean,
    default: false,
  },
  width: {
    type: [String, Number] as PropType<string | number>,
    default: '100%',
  },
  height: {
    type: [String, Number] as PropType<string | number>,
    default: '100%',
  },
  language: {
    type: String as PropType<string>,
    default: 'javascript',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  theme: {
    type: String as PropType<Theme>,
    validator(value: string): boolean {
      return ['vs', 'hc-black', 'vs-dark', 'hc-light'].includes(value);
    },
    default: 'vs-dark',
  },
  options: {
    type: Object as PropType<Options>,
    default() {
      return {
        automaticLayout: true,
        // foldingStrategy: 'indentation',
        foldingStrategy: 'indentation', // 折叠方式  auto | indentation
        // renderLineHighlight: 'all',
        renderLineHighlight: 'all' || 'line' || 'none' || 'gutter', // 行亮
        selectOnLineNumbers: true, // 显示行号
        minimap: {
          // 关闭小地图
          enabled: false,
        },
        placeholder: 'ss',
        // readOnly: false, // 只读
        fontSize: 16, // 字体大小
        scrollBeyondLastLine: false, // 取消代码后面一大段空白
        overviewRulerBorder: false, // 不要滚动条的边框
      };
    },
  },
};
