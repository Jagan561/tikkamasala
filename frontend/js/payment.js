/**
 * Razorpay payment flow.
 * In DEMO_MODE (when backend returns demo_mode:true), bypasses Razorpay SDK
 * and simulates a successful payment instantly.
 */
async function initiatePayment(orderId) {
  const btn = document.getElementById('pay-btn');
  setLoading(btn, true, 'Preparing payment...');
  try {
    // Step 1: Create payment order on backend
    const payData = await api.post('/api/payments/create', { order_id: orderId });

    // Step 2: DEMO MODE — skip Razorpay SDK, go straight to verify
    if (payData.demo_mode || payData.razorpay_key_id === 'DEMO_MODE') {
      showToast('Demo mode — simulating payment...', 'info');
      setTimeout(async () => {
        await verifyPayment({
          razorpay_order_id: payData.razorpay_order_id,
          razorpay_payment_id: 'demo_pay_' + Date.now(),
          razorpay_signature: 'demo_signature',
        }, orderId);
      }, 1200);
      setLoading(btn, false, 'Pay Now');
      return;
    }

    // Step 3: PRODUCTION — open Razorpay checkout
    const user = getUser();
    const options = {
      key: payData.razorpay_key_id,
      amount: payData.amount,
      currency: payData.currency,
      name: 'Tikka Masala Chat Corner',
      description: `Order #${payData.order_number}`,
      image: 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=100',
      order_id: payData.razorpay_order_id,
      handler: async function(response) {
        await verifyPayment(response, orderId);
      },
      prefill: {
        name: user.name || '',
        contact: user.mobile || '',
      },
      theme: { color: '#C8102E' },
      modal: {
        ondismiss: function() {
          showToast('Payment was cancelled.', 'warning');
          setLoading(btn, false, 'Pay Now');
        }
      }
    };

    const rzp = new Razorpay(options);
    rzp.open();
    setLoading(btn, false, 'Pay Now');
  } catch (err) {
    showToast(err.message, 'error');
    setLoading(btn, false, 'Pay Now');
  }
}

async function verifyPayment(response, orderId) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.remove('hidden');
  try {
    const result = await api.post('/api/payments/verify', {
      razorpay_order_id: response.razorpay_order_id,
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_signature: response.razorpay_signature,
    });
    window.location.href = `/customer/order-success.html?order_id=${result.order_id}&order_number=${result.order_number}`;
  } catch (err) {
    showToast('Payment verification failed: ' + err.message, 'error');
    if (overlay) overlay.classList.add('hidden');
  }
}
