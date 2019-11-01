module.exports = async function (req, res, proceed) {

  if (sails.config.token.token_value && sails.config.token === 'admin') {
    return proceed();
  }

  //--•
  // Otherwise, this request did not come from a logged-in user.
  return res.redirect('/admin_login');

};
