import { isArray, isObject } from './is';

export function parseTableRecords(records) {
  const data_li = [];
  for (let i = 0; i < records.length; i++) {
    const record = records[i];
    const dic = {};
    for (const i in record) {
      if (isObject(record[i]) || isArray(record[i])) {
        dic[i] = JSON.stringify(record[i]);
      } else {
        dic[i] = record[i];
      }
    }
    // @ts-ignore
    data_li.push(dic);
  }
  return data_li;
}
