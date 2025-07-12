import { Graph } from '@antv/x6';
import { h } from 'vue';
import Node from './Node.vue';
// 注册菜单节点
Graph.registerNode('menu-node', {
  inherit: 'rect',
  width: 280,
  height: 30,
  img: 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ',
  markup: [
    {
      tagName: 'rect',
      selector: 'body',
    },
    {
      tagName: 'image',
    },
    {
      tagName: 'text',
      selector: 'label',
    },
  ],
  attrs: {
    body: {
      stroke: '#fff',
      fill: '#fff',
    },
    image: {
      width: 26,
      height: 26,
      refY: 1,
      refX: 5,
    },
    label: {
      refX: 100,
      textAnchor: 'middle',
      textVerticalAnchor: 'middle',
      fontSize: 14,
      fill: '#333',
    },
  },
});

// 注册拖拽放置节点
Graph.registerNode('container-node', {
  inherit: 'vue-shape',
  width: 180,
  height: 40,
  img: 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ',
  component: {
    render() {
      return h(Node);
    },
  },
  attrs: {
    body: {
      rx: 6,
      ry: 6,
    },
  },
  ports: {
    groups: {
      top: {
        position: 'top',
        attrs: {
          circle: {
            r: 4,
            magnet: true,
            stroke: '#5F95FF',
            strokeWidth: 1,
            fill: '#fff',
            style: {
              visibility: 'hidden',
            },
          },
        },
      },
      // right: {
      //   position: 'right',
      //   attrs: {
      //     circle: {
      //       r: 4,
      //       magnet: true,
      //       stroke: '#5F95FF',
      //       strokeWidth: 1,
      //       fill: '#fff',
      //       style: {
      //         visibility: 'hidden',
      //       },
      //     },
      //   },
      // },
      bottom: {
        position: 'bottom',
        attrs: {
          circle: {
            r: 4,
            magnet: true,
            stroke: '#5F95FF',
            strokeWidth: 1,
            fill: '#fff',
            style: {
              visibility: 'hidden',
            },
          },
        },
      },
      // left: {
      //   position: 'left',
      //   attrs: {
      //     circle: {
      //       r: 4,
      //       magnet: true,
      //       stroke: '#5F95FF',
      //       strokeWidth: 1,
      //       fill: '#fff',
      //       style: {
      //         visibility: 'hidden',
      //       },
      //     },
      //   },
      // },
    },
    items: [
      {
        group: 'top',
      },
      // {
      //   group: 'right',
      // },
      {
        group: 'bottom',
      },
      // {
      //   group: 'left',
      // },
    ],
  },
});
