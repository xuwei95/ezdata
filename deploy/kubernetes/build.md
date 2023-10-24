```
helm dependency update ./ezdata
helm install ezdata-helm ./ezdata --debug -n ezdata-helm
helm uninstall ezdata-helm ./ezdata --debug -n ezdata-helm
```