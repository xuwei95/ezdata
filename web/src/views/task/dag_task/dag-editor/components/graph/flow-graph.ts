import { Graph, Addon, Model } from '@antv/x6';
import '@antv/x6-vue-shape';
import './shapes';
import { MenuData, MenuGroup } from './types';
import graphSettings from './graph-setting';
import FromJSONData = Model.FromJSONData;

export default class FlowGraph {
  // x6的graph实例，中间画布绘制部分
  public static graph: Graph;

  // x6的stencil实例，左侧菜单部分
  private static stencil: Addon.Stencil;

  /**
   * 初始化画布
   * @param cElement 中间画布的html元素
   */
  static create(cElement: HTMLElement): Graph {
    // 判断是否为空，如果只要有一个为空则抛出异常
    if (!cElement) throw new Error("Can't create graph ,no element'");
    // @ts-ignore
    // 初始化graph
    this.graph = new Graph(graphSettings(cElement));
    // 加载画布中事件
    this.initEvents(cElement);
    return this.graph;
  }

  /**
   * 初始化左侧菜单
   * @param sElement 左侧菜单的html元素
   * @param menuData
   * @private
   */
  static initStencil(sElement: HTMLElement, menuData: any[]): Addon.Stencil {
    const { graph } = this;

    const tmpMenuData: MenuData = this.transformMenuData(menuData);

    this.stencil = new Addon.Stencil({
      // 左侧菜单的总览标题
      title: '组件列表',
      // 拖拽放置目标
      target: graph,
      // 是否可以搜索
      // eslint-disable-next-line @typescript-eslint/no-unused-vars,no-unused-vars
      search: (cell, keyword, groupName, stencil) => {
        console.log(cell, groupName, stencil);
        if (keyword) {
          // @ts-ignore
          return cell?.attr('text/text')?.includes(keyword);
        }
        return true;
      },
      // 搜索框提示文字
      placeholder: '搜索',
      // 无数据提示
      notFoundText: '无数据',
      // 宽高
      stencilGraphWidth: 280,
      stencilGraphHeight: 180,
      // 是否可以折叠
      collapsable: true,
      groups: tmpMenuData.groups,
      // 布局相关信息
      layoutOptions: {
        columns: 1,
        columnWidth: 'compact',
        rowHeight: 'compact',
        dx: 5,
        dy: 5,
        resizeToFit: true,
      },
      // 拖拽放置的节点渲染规则
      getDropNode(node, options) {
        console.log('move666', node, options);
        const params = node.data;
        const img = params.img;
        delete params.img;
        return graph.createNode({
          shape: 'container-node',
          // 如果需要给Node.vue组件传入什么值，在这里进行修改
          data: {
            img: img,
            label: node['label'] || 'no name',
            params: params,
            status: '',
          },
        });
      },
    });
    // 将x6生成的菜单拓展到html对应的位置上
    sElement?.appendChild(this.stencil.container);
    this.initStencilNode(tmpMenuData);
    return this.stencil;
  }

  /**
   *  初始化菜单节点
   * @param subMenuData 子节点数据
   * @private
   */
  private static initStencilNode(subMenuData: MenuData): void {
    Object.keys(subMenuData.items).forEach((key) => {
      this.stencil.load(subMenuData.items[key], key);
    });
  }

  /**
   * 将业务层的菜单数据进行数据转换，转换成渲染需要的数据结构，想了解的可以深入跟踪下代码执行
   * @param menuGroups
   * @private
   */
  private static transformMenuData(menuGroups: MenuGroup[]): MenuData {
    const menuData: MenuData = {
      groups: [],
      items: {},
    };
    menuGroups?.forEach((menuGroup) => {
      // @ts-ignore
      menuData.groups.push({
        title: menuGroup.title,
        name: menuGroup.name,
      });
      // @ts-ignore
      menuData.items[menuGroup.name] = [];
      menuGroup?.children?.forEach((child) => {
        // @ts-ignore
        console.log('init666', child);
        const params = child.params;
        params['img'] = child.img;
        menuData.items[menuGroup.name].push({
          shape: 'menu-node',
          label: child.name,
          data: params,
          attrs: {
            image: {
              'xlink:href': child.img,
            },
          },
        });
      });
    });
    console.log('menu66', menuData);
    return menuData;
  }

  private static initEvents(cElement: HTMLElement): void {
    // 控制连接桩显示/隐藏
    const showPorts = (ports: NodeListOf<SVGElement>, show: boolean) => {
      for (let i = 0, len = ports.length; i < len; i += 1) {
        ports[i].style.visibility = show ? 'visible' : 'hidden';
      }
    };
    const { graph } = this;
    // 右击菜单
    graph.on('node:contextmenu', () => {
      const cells = graph.getSelectedCells();
      console.log('contextmenu', cells);
      // showContextMenu.value = true;
      // nextTick(() => {
      //   const parentRect = document.getElementById('container').getBoundingClientRect();
      //   this.$refs.menuBar.initFn(e.clientX - parentRect.x, e.clientY - parentRect.y, { type: 'node', item: node })
      // })
    });
    // 监听节点鼠标进入事件
    graph.on('node:mouseenter', () => {
      const container = cElement!;
      const ports = container.querySelectorAll('.x6-port-body') as NodeListOf<SVGElement>;
      showPorts(ports, true);
    });
    // 监听节点鼠标离开事件
    graph.on('node:mouseleave', () => {
      const container = cElement!;
      const ports = container.querySelectorAll('.x6-port-body') as NodeListOf<SVGElement>;
      showPorts(ports, false);
    });
    // 快捷键与事件
    // 复制
    graph.bindKey(['meta+c', 'ctrl+c'], () => {
      const cells = graph.getSelectedCells();
      if (cells.length) {
        graph.copy(cells);
      }
      return false;
    });
    // 剪切
    graph.bindKey(['meta+x', 'ctrl+x'], () => {
      const cells = graph.getSelectedCells();
      if (cells.length) {
        graph.cut(cells);
      }
      return false;
    });
    // 粘贴
    graph.bindKey(['meta+v', 'ctrl+v'], () => {
      if (!graph.isClipboardEmpty()) {
        const cells = graph.paste({ offset: 32 });
        graph.cleanSelection();
        graph.select(cells);
      }
      return false;
    });

    // 撤销
    graph.bindKey(['meta+z', 'ctrl+z'], () => {
      if (graph.history.canUndo()) {
        graph.history.undo();
      }
      return false;
    });
    // 还原
    graph.bindKey(['meta+shift+z', 'ctrl+shift+z'], () => {
      if (graph.history.canRedo()) {
        graph.history.redo();
      }
      return false;
    });

    // 选中全部
    graph.bindKey(['meta+a', 'ctrl+a'], () => {
      const nodes = graph.getNodes();
      if (nodes) {
        graph.select(nodes);
      }
    });

    // 删除
    // graph.bindKey('backspace', () => {
    //   const cells = graph.getSelectedCells();
    //   if (cells.length) {
    //     graph.removeCells(cells);
    //   }
    // });
  }

  /**
   * 通过数据进行图形绘制
   * @param graphData
   */
  static reloadGraph(graphData: FromJSONData): void {
    this.graph.fromJSON(graphData);
  }
}
