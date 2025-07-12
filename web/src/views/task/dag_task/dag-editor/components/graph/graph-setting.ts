import { Shape } from '@antv/x6';
import SimpleNodeView from './minimap-view';

/**
 * 图形配置设置
 * @param cElement
 */
const graphSettings = (cElement: HTMLElement) => {
  return {
    container: cElement,
    width: cElement.offsetWidth,
    height: cElement.offsetHeight,
    minimap: {
      enabled: false, // 是否展示小地图
      container: cElement,
      width: 200,
      height: 130,
      graphOptions: {
        async: true,
        // eslint-disable-next-line consistent-return
        getCellView: (cell: any) => {
          if (cell.isNode()) {
            return SimpleNodeView;
          }
        },
        // eslint-disable-next-line consistent-return
        createCellView: (cell: any) => {
          if (cell.isEdge()) {
            return null;
          }
        },
      },
    },
    panning: {
      // 画布平移
      enabled: true, // 是否开启
      eventTypes: ['leftMouseDown'], // 必须通过鼠标左键按下触发
    },
    background: {
      color: 'rgba(255,251,230,0.35)', // 设置画布背景颜色
    },
    grid: true, // 网格
    autoResize: true, // 是否监听容器大小改变，并自动更新画布大小。默认监听画布容器，也可以指定监听的元素，如 Document。
    translating: { restrict: true }, // 配置节点的可移动区域restrict 支持以下几种类型： restrict设置为 true，节点移动时无法超过画布区域。
    mousewheel: {
      enabled: true, // enabled 是否开启滚轮缩放交互。
      zoomAtMousePosition: true, // 是否将鼠标位置作为中心缩放，默认为 true。
      // modifiers: 'ctrl', // 设置修饰键后需要按下修饰键并滚动鼠标滚轮时才触发画布缩放。
      minScale: 0.5, // 最小缩放
      maxScale: 3, // 最大缩放
    },
    connecting: {
      // 连线规则
      router: {
        name: 'manhattan',
        args: {
          padding: 30,
        },
      },
      connector: {
        name: 'rounded',
        args: {
          radius: 6,
        },
      },
      anchor: 'center',
      connectionPoint: 'anchor',
      allowBlank: false, // 是否允许连接到画布空白位置的点，默认为 true。
      snap: {
        radius: 30, // 可以通过配置 radius 属性自定义触发吸附的距离。当 snap 设置为 false 时不会触发自动吸附。默认值为 false。
      },
      createEdge() {
        return new Shape.Edge({
          attrs: {
            line: {
              stroke: '#A2B1C3',
              strokeWidth: 1,
              targetMarker: {
                name: 'block',
                width: 10,
                height: 6,
              },
            },
          },
          zIndex: 0,
        });
      },
      validateConnection({ targetMagnet }: { targetMagnet: any }) {
        return !!targetMagnet;
      },
    },
    highlighting: {
      magnetAdsorbed: {
        name: 'stroke',
        args: {
          attrs: {
            fill: '#fff',
            stroke: '#31d0c6',
            strokeWidth: 4,
          },
        },
      },
    },
    selecting: {
      enabled: true,
      multiple: true,
      rubberEdge: true,
      rubberNode: true,
      modifiers: 'shift',
    },
    snapline: true, // 对齐线
    keyboard: true, // 键盘快捷键
    clipboard: true, // 剪切板
    history: true,
  };
};
export default graphSettings;
