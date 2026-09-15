// Checkout HTTP layer — thin: map request body to named fields, call controller.
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (checkoutController) => {
  const router = express.Router();

  router.post(
    '/api/checkout',
    asyncHandler(async (req, res) => {
      const result = await checkoutController.checkout({
        name: req.body.usr,
        email: req.body.eml,
        password: req.body.pwd,
        courseId: req.body.c_id,
        card: req.body.card,
      });
      res.status(200).json(result);
    })
  );

  return router;
};
