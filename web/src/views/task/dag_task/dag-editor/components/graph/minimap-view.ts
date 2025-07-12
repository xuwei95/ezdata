/**
 * 小地图 自定义展示
 */

import { NodeView } from '@antv/x6';

export default class SimpleNodeView extends NodeView {
  protected renderMarkup() {
    return this.renderJSONMarkup({
      tagName: 'rect',
      selector: 'body',
    });
  }

  update() {
    super.update({
      body: {
        refWidth: '100%',
        refHeight: '100%',
        // fill: 'rgba(1,195,194,0.5)',
      },
    });
  }
}
