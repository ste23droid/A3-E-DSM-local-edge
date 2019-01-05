function (keys, values, rereduce) {
  var stdDeviation=0.0;
  var count=0;
  var total=0.0;
  var sqrTotal=0.0;

  if (!rereduce) {
    // we are reducing over the leaf nodes of the Btree, which are the emitted values from the map function
    for(var i in values) {
      total = total + values[i];
      sqrTotal = sqrTotal + (values[i] * values[i]);
    }
    count = values.length;
  } else {
    // rereduce phase, we are reducing on internal nodes of the Btree, reducing previously reduced values
    for(var i in values) {
      count = count + values[i].count;
      total = total + values[i].total;
      sqrTotal = sqrTotal + values[i].sqrTotal;
    }
  }

  var variance =  (sqrTotal - ((total * total)/count)) / count;
  var average = total / count;
  stdDeviation = Math.sqrt(variance);

  return {"average": average,
          "stdDeviation":stdDeviation,
          "count":count,
          "total":total,
          "sqrTotal":sqrTotal};
}
